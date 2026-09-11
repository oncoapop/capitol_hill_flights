"""
Master Analysis Orchestrator
Runs all Section 2 and Section 4 modules and compiles a unified results.json.
Also generates Table 2 (monthly summary) computed directly from data/capitol_hill_all_flights.csv.

Inputs: data/capitol_hill_all_flights.csv, StatCan files
Output: analysis/results.json, analysis/monthly_summary_recomputed.csv
Date: 2026-09-10
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import json
import numpy as np
import pandas as pd

import section2_1_coverage_passes
import section2_2_changepoint
import section2_3_categorisation
import section2_4_rate_ratios
import section2_5_altitude_proximity
import section2_6_direction
import section2_7_corridor_truncation
import section2_8_seasonality
import section2_9_statcan
import section4_helicopters

RAW_FILE = Path("data/capitol_hill_all_flights.csv")
OUT_JSON = Path("analysis/results.json")
OUT_TABLE2_CSV = Path("analysis/monthly_summary_recomputed.csv")

def generate_recomputed_table2():
    print("Generating recomputed Table 2 from record-level data...")
    df = pd.read_csv(RAW_FILE)
    df["month"] = df["date"].str[:7]
    
    daily = df.groupby(["month", "date"]).size().reset_index(name="daily_count")
    
    monthly_rows = []
    for m, g in daily.groupby("month"):
        counts = g["daily_count"].values
        sub_raw = df[df["month"] == m]
        n_days = len(counts)
        tot = len(sub_raw)
        u_ac = sub_raw["icao"].nunique()
        mean = float(np.mean(counts))
        sem = float(np.std(counts, ddof=1) / np.sqrt(n_days)) if n_days > 1 else 0.0
        med = float(np.median(counts))
        mn = int(np.min(counts))
        mx = int(np.max(counts))
        monthly_rows.append({
            "month": m,
            "total_flights": tot,
            "days_with_data": n_days,
            "min_daily": mn,
            "max_daily": mx,
            "median_daily": med,
            "mean_daily": round(mean, 1),
            "sem_daily": round(sem, 2),
            "unique_aircraft": u_ac
        })
        
    mdf = pd.DataFrame(monthly_rows)
    mdf.to_csv(OUT_TABLE2_CSV, index=False)
    print(f"Saved recomputed monthly summary table to {OUT_TABLE2_CSV}")
    print(f"Table 2 Total Flights Sum: {mdf['total_flights'].sum()} (Target: 20093)")
    print(f"Table 2 Total Days Sum: {mdf['days_with_data'].sum()} (Target: 573)")
    print(f"Overall maximum single-day count: {mdf['max_daily'].max()}")
    return monthly_rows

def main():
    print("=== BUILDING ALL ANALYSES FROM SINGLE SOURCE OF TRUTH ===")
    
    r2_1 = section2_1_coverage_passes.run()
    r2_2 = section2_2_changepoint.run()
    r2_3 = section2_3_categorisation.run()
    r2_4 = section2_4_rate_ratios.run()
    r2_5 = section2_5_altitude_proximity.run()
    r2_6 = section2_6_direction.run()
    r2_7 = section2_7_corridor_truncation.run()
    r2_8 = section2_8_seasonality.run()
    r2_9 = section2_9_statcan.run()
    r4 = section4_helicopters.run()
    table2 = generate_recomputed_table2()
    
    # Fleet composition (M3)
    df_raw = pd.read_csv(RAW_FILE)
    b7xx_count = int(df_raw["type_code"].str.startswith("B7", na=False).sum())
    dh8d_count = int((df_raw["type_code"] == "DH8D").sum())
    c172_count = int((df_raw["type_code"] == "C172").sum())
    b38m_count = int((df_raw["type_code"] == "B38M").sum())
    b738_count = int((df_raw["type_code"] == "B738").sum())
    tot_rec = len(df_raw)
    
    # Diurnal & Night traffic (M4)
    # Check cpa_hour_local for night traffic: 23:00 to 05:59
    night_count = int(df_raw["cpa_hour_local"].isin([23, 0, 1, 2, 3, 4, 5]).sum())
    night_pct = float(night_count / tot_rec * 100.0)
    
    master = {
        "metadata": {
            "source_file": str(RAW_FILE),
            "date_generated": "2026-09-10",
            "study_period": "2025-01-01 to 2026-08-31"
        },
        "section2_1_coverage_passes": r2_1,
        "section2_2_changepoint": r2_2,
        "section2_3_categorisation": r2_3,
        "section2_4_rate_ratios": r2_4,
        "section2_5_altitude_proximity": r2_5,
        "section2_6_direction": r2_6,
        "section2_7_corridor_truncation": r2_7,
        "section2_8_seasonality": r2_8,
        "section2_9_statcan": r2_9,
        "section4_helicopters": r4,
        "table2_monthly_summary": table2,
        "fleet_composition_m3": {
            "DH8D": {"count": dh8d_count, "pct": float(dh8d_count / tot_rec * 100.0)},
            "C172": {"count": c172_count, "pct": float(c172_count / tot_rec * 100.0)},
            "B38M": {"count": b38m_count, "pct": float(b38m_count / tot_rec * 100.0)},
            "B738": {"count": b738_count, "pct": float(b738_count / tot_rec * 100.0)},
            "Boeing_7xx_family": {"count": b7xx_count, "pct": float(b7xx_count / tot_rec * 100.0)}
        },
        "diurnal_night_traffic_m4": {
            "night_hours": "23:00 - 05:59",
            "night_count": night_count,
            "total_records": tot_rec,
            "night_pct": night_pct
        }
    }
    
    with open(OUT_JSON, "w") as f:
        json.dump(master, f, indent=2)
    print(f"\nSuccessfully generated master results file: {OUT_JSON}")

if __name__ == "__main__":
    main()
