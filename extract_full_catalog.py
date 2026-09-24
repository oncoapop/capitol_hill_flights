import argparse
import json
import logging
import sqlite3
import sys
import tarfile
import time
import math
from pathlib import Path
from typing import Dict, Any
from stream_reader import ConcatStreamReader

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger("regional_extractor")

LAT_MIN, LAT_MAX = 49.10, 49.40
LON_MIN, LON_MAX = -123.35, -122.50
CENTER_LAT, CENTER_LON = 49.2869, -122.9853

DB_PATH = Path("regional_full_vancouver.db")
CATALOG_PATH = Path(".releases_catalog.json")
EARTH_RADIUS_KM = 6371.0088

def haversine_km(lat1, lon1, lat2, lon2):
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2.0)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2.0)**2
    return 2.0 * EARTH_RADIUS_KM * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

def init_db():
    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS regional_flights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period TEXT NOT NULL,
            date TEXT NOT NULL,
            icao TEXT NOT NULL,
            callsign TEXT,
            type_code TEXT,
            first_ts REAL,
            last_ts REAL,
            min_alt REAL,
            max_alt REAL,
            
            
            num_points INTEGER,
            trajectory_json TEXT NOT NULL
        )""")
        conn.execute("""
        CREATE TABLE IF NOT EXISTS daily_summary (
            date TEXT PRIMARY KEY,
            period TEXT NOT NULL,
            total_unique_flights INTEGER,
            traces_scanned INTEGER,
            status TEXT
        )""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_reg_period ON regional_flights(period)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_reg_date ON regional_flights(date)")
        

def get_completed_dates():
    if not DB_PATH.exists(): return set()
    with sqlite3.connect(str(DB_PATH)) as conn:
        c = conn.cursor()
        c.execute("SELECT date FROM daily_summary WHERE status='completed'")
        return {r[0] for r in c.fetchall()}

def process_day(date_str: str, release_info: Dict[str, Any]):
    # Infer period from date
    ym = date_str[:7]
    period = ym # e.g. "2025-01"
    
    urls = [a["url"] for a in release_info["assets"]]
    stream = ConcatStreamReader(urls)
    scanned = 0
    matched_flights = []
    start_time = time.time()
    
    try:
        with tarfile.open(fileobj=stream, mode="r|*") as tar:
            for member in tar:
                if not member.name.endswith(".json") or "trace_full_" not in member.name: continue
                scanned += 1
                ef = tar.extractfile(member)
                if not ef: continue
                raw_bytes = ef.read()
                if not raw_bytes: continue
                
                if raw_bytes[:2] == b"\x1f\x8b":
                    try:
                        import gzip
                        decompressed = gzip.decompress(raw_bytes)
                    except: continue
                else:
                    decompressed = raw_bytes
                    
                if b"49." in decompressed and (b"-122." in decompressed or b"-123." in decompressed):
                    try:
                        data = json.loads(decompressed.decode("utf-8", errors="replace"))
                        trace = data.get("trace", [])
                        base_ts = data.get("timestamp", 0.0)
                        
                        # Extract points inside bounding box
                        in_box_pts = []
                        for pt in trace:
                            if len(pt) < 3 or pt[1] is None or pt[2] is None: continue
                            lat, lon = pt[1], pt[2]
                            if LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX:
                                alt = pt[3] if len(pt) > 3 and pt[3] is not None else None
                                trk = pt[5] if len(pt) > 5 and pt[5] is not None else None
                                t_offset = pt[0] if pt[0] is not None else 0.0
                                in_box_pts.append([round(lat, 4), round(lon, 4), alt, round(trk, 1) if trk is not None else None, round(base_ts + t_offset, 1)])
                                
                        if not in_box_pts: continue
                        
                        # SPLIT LOGIC (Time Gaps > 20 mins or >15 mins on ground)
                        segments = []
                        current_seg = [in_box_pts[0]]
                        time_below_1000_start = in_box_pts[0][4] if (in_box_pts[0][2] is not None and in_box_pts[0][2] < 1000) else None
                        
                        for i in range(1, len(in_box_pts)):
                            p1, p2 = in_box_pts[i-1], in_box_pts[i]
                            time_gap = p2[4] - p1[4]
                            alt2 = p2[2] if p2[2] is not None else 0
                            
                            split = False
                            if time_gap > 1200:
                                split = True
                                time_below_1000_start = None
                            else:
                                if alt2 < 1000:
                                    if time_below_1000_start is None: time_below_1000_start = p2[4]
                                else:
                                    if time_below_1000_start is not None and (p2[4] - time_below_1000_start) > 900:
                                        split = True
                                    time_below_1000_start = None
                                    
                            if split and len(current_seg) > 5:
                                segments.append(current_seg)
                                current_seg = []
                                
                            current_seg.append(p2)
                            
                        if len(current_seg) > 5:
                            segments.append(current_seg)
                            
                        # Process distinct flights
                        for seg in segments:
                            min_alt, max_alt = 999999, -999999
                            first_alt, last_alt = None, None
                            
                            
                            for pt in seg:
                                alt = pt[2]
                                if alt is not None:
                                    if first_alt is None: first_alt = alt
                                    last_alt = alt
                                    if alt < min_alt: min_alt = alt
                                    if alt > max_alt: max_alt = alt
                                
                                    
                            if min_alt == 999999: min_alt = None
                            if max_alt == -999999: max_alt = None
                            
                            # Reduce points to save space
                            if len(seg) > 250:
                                step = max(1, len(seg) // 150)
                                seg = seg[::step]
                                
                            
                            
                            matched_flights.append({
                                "period": period, "date": date_str, "icao": data.get("icao", "").upper(),
                                "callsign": (data.get("flight") or "").strip() or None, "type_code": (data.get("t") or "").strip() or None,
                                "first_ts": seg[0][4], "last_ts": seg[-1][4],
                                "min_alt": min_alt, "max_alt": max_alt,
                                
                                "num_points": len(seg), "trajectory_json": json.dumps(seg)
                            })
                    except Exception as e:
                        pass
                        
        duration = time.time() - start_time
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute("BEGIN TRANSACTION;")
            conn.executemany("""
            INSERT INTO regional_flights (
                period, date, icao, callsign, type_code, first_ts, last_ts,
                min_alt, max_alt, num_points, trajectory_json
            ) VALUES (
                :period, :date, :icao, :callsign, :type_code, :first_ts, :last_ts,
                :min_alt, :max_alt, :num_points, :trajectory_json
            )
            """, matched_flights)
            conn.execute("""
            INSERT OR REPLACE INTO daily_summary (
                date, period, total_unique_flights, traces_scanned, status
            ) VALUES (?, ?, ?, ?, 'completed')
            """, (date_str, period, len(matched_flights), scanned))
            conn.commit()
        logger.info(f"✓ [{date_str}] DONE. Found {len(matched_flights)} unique flights in {duration:.1f}s")
    except Exception as e:
        logger.error(f"[{date_str}] FAILED: {e}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=str, default="2025-01")
    parser.add_argument("--end", type=str, default="2026-08")
    args = parser.parse_args()
    
    init_db()
    
    with open(CATALOG_PATH) as f:
        catalog = json.load(f)
        
    completed = get_completed_dates()
    
    dates_to_process = []
    for d in sorted(catalog.keys()):
        ym = d[:7] # e.g. "2025-01"
        if args.start <= ym <= args.end:
            if d not in completed:
                dates_to_process.append(d)
                
    logger.info(f"Processing {len(dates_to_process)} days from {args.start} to {args.end}")
    
    for d in dates_to_process:
        process_day(d, catalog[d])

if __name__ == "__main__":
    main()
