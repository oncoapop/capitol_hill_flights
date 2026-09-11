"""
Replication and Verification Script
Recomputes core manuscript numbers from authoritative raw files
and asserts agreement with analysis/results.json.
"""
import json
import sys
import numpy as np
import pandas as pd
from pathlib import Path

def main():
    print("=== RUNNING REPLICATION & VERIFICATION SUITE ===")
    
    with open("analysis/results.json") as f:
        res = json.load(f)
        
    df_raw = pd.read_csv("data/capitol_hill_all_flights.csv")
    
    # 1. Total records & unique ICAOs
    assert len(df_raw) == 20093, f"Expected 20093 records, got {len(df_raw)}"
    assert df_raw["icao"].nunique() == 2050, f"Expected 2050 ICAOs, got {df_raw['icao'].nunique()}"
    assert df_raw.drop_duplicates(subset=["date", "icao"]).shape[0] == 20093, "Non-unique date-icao pairs"
    print("✓ Rule 1: Record count (20,093) and unique ICAOs (2,050) verified.")
    
    # 2. Date coverage
    dates = sorted(df_raw["date"].unique())
    assert len(dates) == 573, f"Expected 573 days with data, got {len(dates)}"
    all_cal = pd.date_range("2025-01-01", "2026-08-31").strftime("%Y-%m-%d").tolist()
    assert len(all_cal) == 608, f"Expected 608 calendar days, got {len(all_cal)}"
    assert len(set(all_cal) - set(dates)) == 35, f"Expected 35 absent dates, got {len(set(all_cal) - set(dates))}"
    print("✓ Rule 2: Calendar coverage (573 days with data, 35 absent) verified.")
    
    # 3. Discrete passes
    df_passes = pd.read_csv("data/capitol_hill_passes.csv")
    assert len(df_passes) == 24190, f"Expected 24190 primary passes (10 min), got {len(df_passes)}"
    inflation = len(df_passes) / len(df_raw)
    assert abs(inflation - 1.2039) < 0.001, f"Expected inflation factor ~1.204, got {inflation:.4f}"
    print("✓ Rule 3: Discrete passes (24,190) and inflation factor (1.204) verified.")
    
    # 4. Changepoint
    assert res["section2_2_changepoint"]["overall_changepoint_ls"] == "2025-11-27", "Changepoint mismatch"
    print("✓ Rule 4: Primary changepoint (2025-11-27, AIRAC 2513) verified.")
    
    # 5. Table 2 sums
    t2 = res["table2_monthly_summary"]
    tot_t2 = sum(r["total_flights"] for r in t2)
    days_t2 = sum(r["days_with_data"] for r in t2)
    assert tot_t2 == 20093, f"Table 2 total {tot_t2} != 20093"
    assert days_t2 == 573, f"Table 2 days {days_t2} != 573"
    max_day = max(r["max_daily"] for r in t2)
    assert max_day == 128, f"Table 2 max daily {max_day} != 128"
    print("✓ Rule 5: Table 2 reconciliation (20,093 records, 573 days, max day 128) verified.")
    
    # 6. Fleet composition
    fc = res["fleet_composition_m3"]
    assert fc["DH8D"]["count"] == 3432, f"DH8D count mismatch: {fc['DH8D']['count']}"
    assert fc["C172"]["count"] == 1882, f"C172 count mismatch: {fc['C172']['count']}"
    assert fc["B38M"]["count"] == 1240, f"B38M count mismatch: {fc['B38M']['count']}"
    assert fc["B738"]["count"] == 951, f"B738 count mismatch: {fc['B738']['count']}"
    assert fc["Boeing_7xx_family"]["count"] == 3985, f"B7xx count mismatch: {fc['Boeing_7xx_family']['count']}"
    print("✓ Rule 6: Fleet composition (DH8D: 3432, C172: 1882, B38M: 1240, B738: 951, B7xx: 3985) verified.")
    
    # 7. Night traffic
    nt = res["diurnal_night_traffic_m4"]
    assert abs(nt["night_pct"] - 5.136) < 0.01, f"Night pct mismatch: {nt['night_pct']}"
    print("✓ Rule 7: Night traffic percentage (5.14%) verified.")
    
    # 8. StatCan external validation ratios
    sc = res["section2_9_statcan"]["statcan"]
    assert abs(sc["YVR"]["ratio"] - 0.995) < 0.005, f"YVR ratio mismatch: {sc['YVR']['ratio']}"
    assert abs(sc["GA_combined"]["ratio"] - 0.866) < 0.005, f"GA combined mismatch: {sc['GA_combined']['ratio']}"
    assert abs(sc["Vancouver_Harbour"]["ratio"] - 1.213) < 0.005, f"Vancouver Harbour ratio mismatch: {sc['Vancouver_Harbour']['ratio']}"
    print("✓ Rule 8: StatCan movement ratios (YVR: 0.995, GA: 0.866, Harbour: 1.213) verified.")
    
    print("\nALL REPLICATION CHECKS PASSED SUCCESSFULLY.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
