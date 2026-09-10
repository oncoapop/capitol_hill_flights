"""
SQLite database management for Capitol Hill aircraft flights and processing checkpoints.
"""
import sqlite3
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
import pandas as pd

from config import DATABASE_PATH

logger = logging.getLogger(__name__)


def get_connection(db_path: Path = DATABASE_PATH) -> sqlite3.Connection:
    """Get a SQLite connection with row factory configured."""
    conn = sqlite3.connect(str(db_path), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def init_db(db_path: Path = DATABASE_PATH) -> None:
    """Initialize database schema if not already created."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with get_connection(db_path) as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS flights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            icao TEXT NOT NULL,
            callsign TEXT,
            registration TEXT,
            type_code TEXT,
            type_desc TEXT,
            first_seen_ts REAL,
            last_seen_ts REAL,
            first_seen_utc TEXT,
            last_seen_utc TEXT,
            cpa_ts REAL,
            cpa_utc TEXT,
            cpa_local TEXT,
            cpa_hour_local INTEGER,
            cpa_hour_utc INTEGER,
            min_dist_km REAL,
            min_dist_alt_baro TEXT,
            min_dist_gs REAL,
            min_dist_track REAL,
            min_dist_lat REAL,
            min_dist_lon REAL,
            num_points_in_zone INTEGER,
            total_trace_points INTEGER,
            matched_points_json TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(date, icao, cpa_ts)
        );

        CREATE TABLE IF NOT EXISTS processing_log (
            date TEXT PRIMARY KEY,
            release_tag TEXT,
            repo TEXT,
            status TEXT NOT NULL,
            flights_found INTEGER DEFAULT 0,
            total_traces_scanned INTEGER DEFAULT 0,
            bytes_processed INTEGER DEFAULT 0,
            duration_seconds REAL DEFAULT 0.0,
            error_message TEXT,
            processed_at TEXT DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_flights_date ON flights(date);
        CREATE INDEX IF NOT EXISTS idx_flights_cpa_hour_local ON flights(cpa_hour_local);
        CREATE INDEX IF NOT EXISTS idx_flights_icao ON flights(icao);
        CREATE INDEX IF NOT EXISTS idx_flights_callsign ON flights(callsign);
        CREATE INDEX IF NOT EXISTS idx_flights_type_code ON flights(type_code);
        """)
        conn.commit()


def is_date_completed(date_str: str, db_path: Path = DATABASE_PATH) -> bool:
    """Check if a date has already been successfully processed."""
    with get_connection(db_path) as conn:
        cur = conn.execute(
            "SELECT status FROM processing_log WHERE date = ? AND status = 'completed'",
            (date_str,),
        )
        row = cur.fetchone()
        return row is not None


def get_completed_dates(db_path: Path = DATABASE_PATH) -> Set[str]:
    """Return set of all successfully completed date strings."""
    with get_connection(db_path) as conn:
        cur = conn.execute("SELECT date FROM processing_log WHERE status = 'completed'")
        return {row["date"] for row in cur.fetchall()}


def log_processing_start(
    date_str: str,
    release_tag: str,
    repo: str,
    db_path: Path = DATABASE_PATH,
) -> None:
    """Record that processing for a date has started."""
    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO processing_log (date, release_tag, repo, status, error_message, processed_at)
            VALUES (?, ?, ?, 'in_progress', NULL, datetime('now'))
            ON CONFLICT(date) DO UPDATE SET
                release_tag=excluded.release_tag,
                repo=excluded.repo,
                status='in_progress',
                error_message=NULL,
                processed_at=datetime('now')
            """,
            (date_str, release_tag, repo),
        )
        conn.commit()


def log_processing_complete(
    date_str: str,
    flights_found: int,
    total_traces_scanned: int,
    bytes_processed: int,
    duration_seconds: float,
    status: str = "completed",
    error_message: Optional[str] = None,
    db_path: Path = DATABASE_PATH,
) -> None:
    """Record that processing for a date has completed or failed."""
    with get_connection(db_path) as conn:
        conn.execute(
            """
            UPDATE processing_log
            SET status = ?,
                flights_found = ?,
                total_traces_scanned = ?,
                bytes_processed = ?,
                duration_seconds = ?,
                error_message = ?,
                processed_at = datetime('now')
            WHERE date = ?
            """,
            (
                status,
                flights_found,
                total_traces_scanned,
                bytes_processed,
                duration_seconds,
                error_message,
                date_str,
            ),
        )
        conn.commit()


def insert_flights(flights: List[Dict[str, Any]], db_path: Path = DATABASE_PATH) -> int:
    """
    Insert a list of flight records into the flights table.
    Returns the number of rows inserted.
    """
    if not flights:
        return 0

    sql = """
    INSERT INTO flights (
        date, icao, callsign, registration, type_code, type_desc,
        first_seen_ts, last_seen_ts, first_seen_utc, last_seen_utc,
        cpa_ts, cpa_utc, cpa_local, cpa_hour_local, cpa_hour_utc,
        min_dist_km, min_dist_alt_baro, min_dist_gs, min_dist_track,
        min_dist_lat, min_dist_lon, num_points_in_zone, total_trace_points,
        matched_points_json
    ) VALUES (
        :date, :icao, :callsign, :registration, :type_code, :type_desc,
        :first_seen_ts, :last_seen_ts, :first_seen_utc, :last_seen_utc,
        :cpa_ts, :cpa_utc, :cpa_local, :cpa_hour_local, :cpa_hour_utc,
        :min_dist_km, :min_dist_alt_baro, :min_dist_gs, :min_dist_track,
        :min_dist_lat, :min_dist_lon, :num_points_in_zone, :total_trace_points,
        :matched_points_json
    )
    ON CONFLICT(date, icao, cpa_ts) DO UPDATE SET
        callsign=coalesce(excluded.callsign, flights.callsign),
        registration=coalesce(excluded.registration, flights.registration),
        type_code=coalesce(excluded.type_code, flights.type_code),
        type_desc=coalesce(excluded.type_desc, flights.type_desc),
        min_dist_km=excluded.min_dist_km,
        min_dist_alt_baro=excluded.min_dist_alt_baro,
        min_dist_gs=excluded.min_dist_gs,
        min_dist_track=excluded.min_dist_track,
        min_dist_lat=excluded.min_dist_lat,
        min_dist_lon=excluded.min_dist_lon,
        num_points_in_zone=excluded.num_points_in_zone,
        matched_points_json=excluded.matched_points_json
    """

    with get_connection(db_path) as conn:
        conn.executemany(sql, flights)
        conn.commit()

    return len(flights)


def fetch_all_flights_df(db_path: Path = DATABASE_PATH) -> pd.DataFrame:
    """Load all flights from the database into a pandas DataFrame."""
    with get_connection(db_path) as conn:
        df = pd.read_sql_query("SELECT * FROM flights ORDER BY cpa_utc ASC", conn)
    return df


def fetch_processing_summary(db_path: Path = DATABASE_PATH) -> Dict[str, Any]:
    """Fetch status summary across all dates."""
    with get_connection(db_path) as conn:
        cur = conn.execute("""
            SELECT 
                COUNT(*) as total_days_attempted,
                SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as completed_days,
                SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as failed_days,
                SUM(flights_found) as total_flights_found,
                SUM(total_traces_scanned) as total_traces_scanned,
                SUM(bytes_processed) as total_bytes_processed
            FROM processing_log
        """)
        row = dict(cur.fetchone())
        return row
