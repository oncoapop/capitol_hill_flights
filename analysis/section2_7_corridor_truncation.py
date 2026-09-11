"""
Section 2.7: Corridor Geometry and Boundary Truncation Analysis
Localises Eastbound and Westbound arrival corridors and calculates radius-sensitivity curve
to demonstrate boundary truncation of the westbound corridor.

Inputs: data/capitol_hill_all_flights.csv, analysis/aircraft_classification.json
Output: analysis/results_section2_7.json
Date: 2026-09-10
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path

RAW_FILE = Path("data/capitol_hill_all_flights.csv")
MAPPING_FILE = Path("analysis/aircraft_classification.json")
OUT_JSON = Path("analysis/results_section2_7.json")

SUMMIT_LAT = 49.2869

def run():
    print("Running Section 2.7: Corridor Geometry and Boundary Truncation Analysis...")
    with open(MAPPING_FILE) as f:
        mapping = json.load(f)
    comm_types = set(mapping["commercial"])
    
    df = pd.read_csv(RAW_FILE)
    df["alt"] = pd.to_numeric(df["min_dist_alt_baro"], errors="coerce")
    df["track"] = pd.to_numeric(df["min_dist_track"], errors="coerce")
    
    post_arr = df[(df["date"] >= "2025-11-27") & (df["type_code"].isin(comm_types)) & (df["alt"] < 10000)].copy()
    
    # 1. Eastbound (060 - 150 deg)
    eb = post_arr[(post_arr["track"] >= 60.0) & (post_arr["track"] <= 150.0)]
    eb_lat_diff_km = (eb["min_dist_lat"].median() - SUMMIT_LAT) * 111.19
    eb_lat_iqr_m = (eb["min_dist_lat"].quantile(0.75) - eb["min_dist_lat"].quantile(0.25)) * 111190.0
    
    # 2. Westbound (240 - 330 deg)
    wb = post_arr[(post_arr["track"] >= 240.0) & (post_arr["track"] <= 330.0)]
    wb_lat_diff_km = (wb["min_dist_lat"].median() - SUMMIT_LAT) * 111.19
    wb_lat_iqr_m = (wb["min_dist_lat"].quantile(0.75) - wb["min_dist_lat"].quantile(0.25)) * 111190.0
    
    # 3. Radius sensitivity curve (0.1 km to 1.5 km)
    radii = np.arange(0.1, 1.55, 0.1)
    radius_curve = []
    total_post_arr = len(post_arr)
    for r in radii:
        cnt = int((post_arr["min_dist_km"] <= r).sum())
        pct = float(cnt / total_post_arr * 100.0)
        radius_curve.append({
            "radius_km": round(float(r), 2),
            "count": cnt,
            "pct": pct
        })
        
    cnt_1_4 = int((post_arr["min_dist_km"] <= 1.4).sum())
    cnt_1_5 = int((post_arr["min_dist_km"] <= 1.5).sum())
    final_100m_pct = float((cnt_1_5 - cnt_1_4) / cnt_1_5 * 100.0)
    
    results = {
        "eastbound_corridor": {
            "heading_band": "060-150 deg",
            "n": len(eb),
            "median_lat": float(eb["min_dist_lat"].median()),
            "distance_from_summit_km": float(eb_lat_diff_km),
            "median_alt_ft": float(eb["alt"].median()),
            "median_gs_kt": float(eb["min_dist_gs"].median()),
            "median_cpa_dist_km": float(eb["min_dist_km"].median()),
            "lateral_iqr_m": float(eb_lat_iqr_m)
        },
        "westbound_corridor": {
            "heading_band": "240-330 deg",
            "n": len(wb),
            "median_lat": float(wb["min_dist_lat"].median()),
            "distance_from_summit_km": float(wb_lat_diff_km),
            "median_alt_ft": float(wb["alt"].median()),
            "median_gs_kt": float(wb["min_dist_gs"].median()),
            "median_cpa_dist_km": float(wb["min_dist_km"].median()),
            "lateral_iqr_m": float(wb_lat_iqr_m),
            "truncated_by_boundary": True
        },
        "radius_sensitivity": {
            "curve": radius_curve,
            "final_100m_entries_pct": final_100m_pct
        }
    }
    
    with open(OUT_JSON, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved Section 2.7 results to {OUT_JSON}")
    print(json.dumps(results, indent=2))
    return results

if __name__ == "__main__":
    run()
