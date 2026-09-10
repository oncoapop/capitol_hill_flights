"""
Main extraction pipeline: streams ADS-B archives directly from GitHub releases in-memory,
filters flights within 1.5 km of Capitol Hill, Burnaby, BC, and saves results into SQLite.
"""
import argparse
import concurrent.futures
import gzip
import json
import logging
import os
import re
import sys
import time
import urllib.request
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from config import (
    REPOS,
    GITHUB_API_BASE,
    USER_AGENT,
    DATABASE_PATH,
    WORKSPACE_DIR,
)
from database import (
    init_db,
    is_date_completed,
    get_completed_dates,
    log_processing_start,
    log_processing_complete,
    insert_flights,
    fetch_processing_summary,
)
from geo_utils import process_trace_data
from stream_reader import ConcatStreamReader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("pipeline")

CACHE_CATALOG_PATH = WORKSPACE_DIR / ".releases_catalog.json"


def fetch_releases_for_repo(repo_name: str, max_pages: int = 15) -> List[Dict[str, Any]]:
    """Fetch all release metadata for a repository from GitHub API."""
    releases = []
    headers = {"User-Agent": USER_AGENT, "Accept": "application/vnd.github.v3+json"}

    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"

    for page in range(1, max_pages + 1):
        url = f"{GITHUB_API_BASE}/{repo_name}/releases?per_page=100&page={page}"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.load(resp)
                if not data or not isinstance(data, list):
                    break
                for r in data:
                    tag = r.get("tag_name", "")
                    if "prod-0" in tag:
                        m = re.search(r"v(\d{4})\.(\d{2})\.(\d{2})-planes-readsb-prod-0", tag)
                        date_str = f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else None

                        assets = []
                        for a in r.get("assets", []):
                            name = a.get("name", "")
                            if name.endswith(".tar") or ".tar.a" in name:
                                assets.append({
                                    "name": name,
                                    "size": a.get("size", 0),
                                    "url": a.get("browser_download_url"),
                                })
                        assets.sort(key=lambda x: x["name"])
                        if date_str and assets:
                            releases.append({
                                "date": date_str,
                                "tag": tag,
                                "repo": repo_name,
                                "assets": assets,
                            })
        except Exception as e:
            logger.warning(f"Error fetching page {page} for {repo_name}: {e}")
            break
    return releases


def load_or_update_catalog(force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
    """
    Load release catalog from disk cache, or fetch from GitHub API if missing/stale.
    Returns mapping: date_str (YYYY-MM-DD) -> release info dict.
    """
    if not force_refresh and CACHE_CATALOG_PATH.exists():
        try:
            with open(CACHE_CATALOG_PATH, "r", encoding="utf-8") as f:
                cached = json.load(f)
                if cached:
                    logger.info(f"Loaded {len(cached)} release archives from local catalog cache.")
                    return cached
        except Exception as e:
            logger.warning(f"Failed to read catalog cache: {e}")

    logger.info("Fetching release metadata from GitHub archives...")
    catalog = {}
    for year, repo in REPOS.items():
        logger.info(f"Scanning {repo}...")
        rel_list = fetch_releases_for_repo(repo)
        logger.info(f"Found {len(rel_list)} prod releases in {repo}.")
        for r in rel_list:
            catalog[r["date"]] = r

    try:
        with open(CACHE_CATALOG_PATH, "w", encoding="utf-8") as f:
            json.dump(catalog, f, indent=2)
        logger.info(f"Saved catalog of {len(catalog)} releases to {CACHE_CATALOG_PATH.name}")
    except Exception as e:
        logger.warning(f"Could not save catalog cache: {e}")

    return catalog


def process_date_archive(
    date_str: str,
    release_info: Dict[str, Any],
    db_path: Path = DATABASE_PATH,
    progress_interval: int = 5000,
) -> Tuple[int, int]:
    """
    Stream and filter archive in-memory for a specific date.
    Returns (flights_found, traces_scanned).
    """
    import tarfile

    tag = release_info["tag"]
    repo = release_info["repo"]
    assets = release_info["assets"]
    urls = [a["url"] for a in assets]

    total_expected_mb = sum(a["size"] for a in assets) / (1024 * 1024)
    logger.info(f"[{date_str}] Starting in-memory stream for {tag} ({len(urls)} parts, ~{total_expected_mb:.1f} MB)...")

    log_processing_start(date_str, tag, repo, db_path=db_path)
    start_time = time.time()

    matched_flights = []
    traces_scanned = 0
    bytes_streamed = 0

    try:
        stream = ConcatStreamReader(urls)
        with tarfile.open(fileobj=stream, mode="r|*") as tar:
            for member in tar:
                if not member.name.endswith(".json") and not member.name.endswith(".json.gz"):
                    continue
                if "trace_full_" not in member.name:
                    continue

                f = tar.extractfile(member)
                if not f or member.size == 0:
                    continue

                raw_bytes = f.read()
                if not raw_bytes:
                    continue

                if raw_bytes[:2] == b"\x1f\x8b":
                    try:
                        decompressed = gzip.decompress(raw_bytes)
                    except Exception:
                        continue
                else:
                    decompressed = raw_bytes

                try:
                    trace_json = json.loads(decompressed.decode("utf-8", errors="replace"))
                except Exception:
                    continue

                traces_scanned += 1
                if traces_scanned % progress_interval == 0:
                    logger.info(
                        f"[{date_str}] Scanned {traces_scanned} aircraft traces | Matched flights: {len(matched_flights)}"
                    )

                flight_record = process_trace_data(trace_json, date_str)
                if flight_record:
                    matched_flights.append(flight_record)
                    logger.info(
                        f"[{date_str}] MATCH #{len(matched_flights)}: ICAO={flight_record['icao']} "
                        f"Type={flight_record['type_code']} Alt={flight_record['min_dist_alt_baro']}ft "
                        f"Time={flight_record['cpa_local']}"
                    )

        duration = time.time() - start_time
        bytes_streamed = stream.total_bytes_read

        if matched_flights:
            insert_flights(matched_flights, db_path=db_path)

        log_processing_complete(
            date_str=date_str,
            flights_found=len(matched_flights),
            total_traces_scanned=traces_scanned,
            bytes_processed=bytes_streamed,
            duration_seconds=round(duration, 2),
            status="completed",
            db_path=db_path,
        )

        logger.info(
            f"[{date_str}] FINISHED in {duration:.1f}s: Scanned {traces_scanned} traces, "
            f"Found {len(matched_flights)} flights over Capitol Hill (Streamed {bytes_streamed/(1024*1024):.1f} MB in-memory)."
        )
        return len(matched_flights), traces_scanned

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"[{date_str}] ERROR during processing: {e}", exc_info=True)
        log_processing_complete(
            date_str=date_str,
            flights_found=len(matched_flights),
            total_traces_scanned=traces_scanned,
            bytes_processed=bytes_streamed,
            duration_seconds=round(duration, 2),
            status="failed",
            error_message=str(e),
            db_path=db_path,
        )
        raise e


def parse_date_arg(date_str: str) -> str:
    """Validate and normalize YYYY-MM-DD string."""
    dt = datetime.strptime(date_str.strip(), "%Y-%m-%d")
    return dt.strftime("%Y-%m-%d")


def select_sample_per_month(available_dates: List[str], count_per_month: int = 1) -> List[str]:
    """Select count_per_month evenly spaced dates for each month in available_dates."""
    from collections import defaultdict
    by_month = defaultdict(list)
    for d in sorted(available_dates):
        month_key = d[:7]  # YYYY-MM
        by_month[month_key].append(d)

    selected = []
    for month_key, dates in sorted(by_month.items()):
        if len(dates) <= count_per_month:
            selected.extend(dates)
        else:
            step = len(dates) / float(count_per_month)
            for i in range(count_per_month):
                idx = int(i * step)
                selected.append(dates[idx])
    return selected


def main():
    parser = argparse.ArgumentParser(description="Capitol Hill Flight Tracking Data Pipeline")
    parser.add_argument("--date", type=str, help="Process a single date (YYYY-MM-DD)")
    parser.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD) inclusive")
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD) inclusive")
    parser.add_argument("--all", action="store_true", help="Process all available dates from 2025-01-01 to present")
    parser.add_argument("--sample-per-month", type=int, default=None, help="Sample N evenly spaced dates per month across the range")
    parser.add_argument("--workers", type=int, default=4, help="Number of concurrent worker threads (default: 4)")
    parser.add_argument("--force", action="store_true", help="Force re-processing of already completed dates")
    parser.add_argument("--catalog-refresh", action="store_true", help="Refresh GitHub releases catalog cache")
    parser.add_argument("--status", action="store_true", help="Print summary status of processed dates and exit")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of dates to process in this run")

    args = parser.parse_args()

    init_db(DATABASE_PATH)

    if args.status:
        summary = fetch_processing_summary(DATABASE_PATH)
        print("=" * 60)
        print("CAPITOL HILL FLIGHT PIPELINE STATUS")
        print("=" * 60)
        print(f"Database: {DATABASE_PATH}")
        print(f"Total Dates Attempted: {summary.get('total_days_attempted') or 0}")
        print(f"Completed Dates:       {summary.get('completed_days') or 0}")
        print(f"Failed Dates:          {summary.get('failed_days') or 0}")
        print(f"Total Flights Matched: {summary.get('total_flights_found') or 0}")
        print(f"Traces Scanned:        {summary.get('total_traces_scanned') or 0}")
        bytes_proc = summary.get('total_bytes_processed') or 0
        print(f"Data Streamed:         {bytes_proc / (1024*1024*1024):.2f} GB")
        print("=" * 60)
        return

    catalog = load_or_update_catalog(force_refresh=args.catalog_refresh)
    if not catalog:
        logger.error("No releases found in catalog.")
        sys.exit(1)

    completed_dates = get_completed_dates(DATABASE_PATH)

    target_dates: List[str] = []

    if args.date:
        target_dates = [parse_date_arg(args.date)]
    elif args.start_date or args.end_date:
        start_d = parse_date_arg(args.start_date) if args.start_date else "2025-01-01"
        end_d = parse_date_arg(args.end_date) if args.end_date else date.today().strftime("%Y-%m-%d")
        
        cur = datetime.strptime(start_d, "%Y-%m-%d").date()
        end_dt = datetime.strptime(end_d, "%Y-%m-%d").date()
        range_dates = []
        while cur <= end_dt:
            range_dates.append(cur.strftime("%Y-%m-%d"))
            cur += timedelta(days=1)
        
        if args.sample_per_month:
            target_dates = select_sample_per_month(range_dates, args.sample_per_month)
        else:
            target_dates = range_dates
    elif args.all or args.sample_per_month:
        all_catalog_dates = [d for d in catalog.keys() if d >= "2025-01-01"]
        if args.sample_per_month:
            target_dates = select_sample_per_month(all_catalog_dates, args.sample_per_month)
        else:
            target_dates = sorted(all_catalog_dates)
    else:
        target_dates = ["2025-01-01"]

    pending_dates = []
    for d in target_dates:
        if d not in catalog:
            continue
        if d in completed_dates and not args.force:
            continue
        pending_dates.append(d)

    if args.limit and len(pending_dates) > args.limit:
        logger.info(f"Limiting run to {args.limit} dates (out of {len(pending_dates)} pending).")
        pending_dates = pending_dates[:args.limit]

    logger.info(f"Targeting {len(pending_dates)} date(s) for extraction using {args.workers} worker(s)...")

    if not pending_dates:
        logger.info("All selected dates are already processed.")
        return

    # Process dates using ThreadPoolExecutor
    workers = max(1, min(args.workers, len(pending_dates)))
    if workers == 1:
        for idx, date_str in enumerate(pending_dates, 1):
            logger.info(f"\n[{idx}/{len(pending_dates)}] Processing date {date_str}...")
            rel_info = catalog[date_str]
            try:
                process_date_archive(date_str, rel_info, db_path=DATABASE_PATH)
            except Exception as e:
                logger.error(f"Failed processing {date_str}: {e}")
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_date = {
                executor.submit(process_date_archive, d, catalog[d], DATABASE_PATH): d
                for d in pending_dates
            }
            completed_count = 0
            for future in concurrent.futures.as_completed(future_to_date):
                d = future_to_date[future]
                completed_count += 1
                try:
                    flights_cnt, traces_cnt = future.result()
                    logger.info(f"[{completed_count}/{len(pending_dates)}] Completed {d}: {flights_cnt} flights matched ({traces_cnt} traces scanned).")
                except Exception as e:
                    logger.error(f"[{completed_count}/{len(pending_dates)}] Failed {d}: {e}")


if __name__ == "__main__":
    main()
