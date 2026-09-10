"""
Unit and integration tests for Capitol Hill flight tracking pipeline.
"""
import unittest
import json
import sqlite3
from pathlib import Path
import tempfile
import io

from config import CENTER_LAT, CENTER_LON, RADIUS_KM
from geo_utils import haversine_distance_km, in_bounding_box, process_trace_data
from stream_reader import ConcatStreamReader
import database


class TestGeoUtils(unittest.TestCase):

    def test_haversine_exact_center(self):
        dist = haversine_distance_km(CENTER_LAT, CENTER_LON, CENTER_LAT, CENTER_LON)
        self.assertAlmostEqual(dist, 0.0, places=5)

    def test_haversine_known_offset(self):
        # 0.01 deg latitude is approx 1.11 km
        dist = haversine_distance_km(CENTER_LAT, CENTER_LON, CENTER_LAT + 0.01, CENTER_LON)
        self.assertTrue(1.0 < dist < 1.2, f"Expected ~1.11 km, got {dist}")

    def test_bounding_box(self):
        # Inside
        self.assertTrue(in_bounding_box(CENTER_LAT, CENTER_LON))
        # Outside (e.g. London UK)
        self.assertFalse(in_bounding_box(51.5074, -0.1278))
        # Outside (e.g. YVR Airport: 49.1947, -123.1792)
        self.assertFalse(in_bounding_box(49.1947, -123.1792))

    def test_process_trace_inside(self):
        raw_data = {
            "icao": "c0ffee",
            "flight": "ACA101",
            "r": "C-ABCD",
            "t": "B738",
            "desc": "BOEING 737-800",
            "timestamp": 1735689600.0,
            "trace": [
                # Far outside
                [10.0, 49.1000, -123.5000, 25000, 450, 90],
                # Inside bounding box and within 1.5km (offset ~0.005 deg)
                [100.0, CENTER_LAT + 0.003, CENTER_LON + 0.002, 3500, 220, 85],
                # Directly over center
                [110.0, CENTER_LAT, CENTER_LON, 3400, 220, 85],
                # Still inside 1.5km
                [120.0, CENTER_LAT - 0.003, CENTER_LON - 0.002, 3300, 220, 85],
                # Leaving area
                [200.0, 49.4000, -122.5000, 3000, 210, 80],
            ],
        }
        res = process_trace_data(raw_data, "2025-01-01")
        self.assertIsNotNone(res)
        self.assertEqual(res["icao"], "C0FFEE")
        self.assertEqual(res["callsign"], "ACA101")
        self.assertEqual(res["type_code"], "B738")
        self.assertAlmostEqual(res["min_dist_km"], 0.0, places=3)
        self.assertEqual(res["min_dist_alt_baro"], "3400")
        self.assertEqual(res["num_points_in_zone"], 3)

    def test_process_trace_outside(self):
        raw_data = {
            "icao": "a1b2c3",
            "flight": "WJA456",
            "timestamp": 1735689600.0,
            "trace": [
                [10.0, 49.1000, -123.5000, 25000, 450, 90],
                [20.0, 49.1200, -123.4000, 24000, 440, 90],
            ],
        }
        res = process_trace_data(raw_data, "2025-01-01")
        self.assertIsNone(res)


class TestDatabase(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_flights.db"
        database.init_db(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_insert_and_retrieve_flights(self):
        flight = {
            "date": "2025-01-01",
            "icao": "C0FFEE",
            "callsign": "ACA101",
            "registration": "C-ABCD",
            "type_code": "B738",
            "type_desc": "BOEING 737-800",
            "first_seen_ts": 1735689700.0,
            "last_seen_ts": 1735689720.0,
            "first_seen_utc": "2025-01-01T00:01:40+00:00",
            "last_seen_utc": "2025-01-01T00:02:00+00:00",
            "cpa_ts": 1735689710.0,
            "cpa_utc": "2025-01-01T00:01:50+00:00",
            "cpa_local": "2024-12-31T16:01:50-08:00",
            "cpa_hour_local": 16,
            "cpa_hour_utc": 0,
            "min_dist_km": 0.25,
            "min_dist_alt_baro": "3400",
            "min_dist_gs": 220.0,
            "min_dist_track": 85.0,
            "min_dist_lat": 49.2869,
            "min_dist_lon": -122.9853,
            "num_points_in_zone": 3,
            "total_trace_points": 5,
            "matched_points_json": "[]",
        }
        inserted = database.insert_flights([flight], self.db_path)
        self.assertEqual(inserted, 1)

        df = database.fetch_all_flights_df(self.db_path)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]["icao"], "C0FFEE")

    def test_checkpointing(self):
        self.assertFalse(database.is_date_completed("2025-01-01", self.db_path))

        database.log_processing_start("2025-01-01", "v2025.01.01-planes-readsb-prod-0", "adsblol/globe_history_2025", self.db_path)
        self.assertFalse(database.is_date_completed("2025-01-01", self.db_path))

        database.log_processing_complete("2025-01-01", flights_found=5, total_traces_scanned=10000, bytes_processed=500000, duration_seconds=12.5, db_path=self.db_path)
        self.assertTrue(database.is_date_completed("2025-01-01", self.db_path))


if __name__ == "__main__":
    unittest.main()
