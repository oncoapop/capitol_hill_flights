"""
Section 2.5: Altitude and Proximity Analysis
Computes medians and IQRs of barometric altitude and 3D slant distance (summit: 115 m ASL)
for commercial arrivals within 500 m of Capitol Hill summit.

Inputs: data/capitol_hill_passes.csv, data/capitol_hill_all_flights.csv, analysis/aircraft_classification.json
Output: analysis/results_section2_5.json
Date: 2026-09-10
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path

PASSES_FILE = Path("data/capitol_hill_passes.csv")
RAW_FILE = Path("data/capitol_hill_all_flights.csv")
MAPPING_FILE = Path("analysis/aircraft_classification.json")
OUT_JSON = Path("analysis/results_section2_5.json")

SUMMIT_ELEV_M = 115.0

def run():
    print("Running Section 2.5: Altitude and Proximity Analysis...")
    with open(MAPPING_FILE) as f:
        mapping = json.load(f)
    comm_types = set(mapping["commercial"])
    
    # Analyze both record level and pass level
    df_raw = pd.read_csv(RAW_FILE)
    df_raw["alt"] = pd.to_numeric(df_raw["min_dist_alt_baro"], errors="coerce")
    df_raw["dz_m"] = df_raw["alt"] * 0.3048 - SUMMIT_ELEV_M
    df_raw["slant_3d_km"] = np.sqrt((df_raw["min_dist_km"] * 1000.0)**2 + df_raw["dz_m"]**2) / 1000.0
    
    df_passes = pd.read_csv(PASSES_FILE)
    df_passes["dz_m"] = df_passes["alt_baro"] * 0.3048 - SUMMIT_ELEV_M
    df_passes["slant_3d_km"] = np.sqrt((df_passes["dist_km"] * 1000.0)**2 + df_passes["dz_m"]**2) / 1000.0
    
    # Filter for commercial arrivals <= 500 m
    ca_raw = df_raw[df_raw["type_code"].isin(comm_types) & (df_raw["alt"] < 10000) & (df_raw["min_dist_km"] <= 0.5)]
    ca_pass = df_passes[df_passes["type_code"].isin(comm_types) & (df_passes["alt_baro"] < 10000) & (df_passes["dist_km"] <= 0.5)]
    
    def get_stats(sub, alt_col):
        pre = sub[sub["date"] < "2025-11-27"]
        post = sub[sub["date"] >= "2025-11-27"]
        return {
            "pre": {
                "n": len(pre),
                "alt_median_ft": float(pre[alt_col].median()),
                "alt_iqr_ft": [float(pre[alt_col].quantile(0.25)), float(pre[alt_col].quantile(0.75))],
                "slant_median_km": float(pre["slant_3d_km"].median()),
                "slant_iqr_km": [float(pre["slant_3d_km"].quantile(0.25)), float(pre["slant_3d_km"].quantile(0.75))]
            },
            "post": {
                "n": len(post),
                "alt_median_ft": float(post[alt_col].median()),
                "alt_iqr_ft": [float(post[alt_col].quantile(0.25)), float(post[alt_col].quantile(0.75))],
                "slant_median_km": float(post["slant_3d_km"].median()),
                "slant_iqr_km": [float(post["slant_3d_km"].quantile(0.25)), float(post["slant_3d_km"].quantile(0.75))]
            }
        }
        
    results = {
        "summit_elevation_m": SUMMIT_ELEV_M,
        "record_level": get_stats(ca_raw, "alt"),
        "pass_level": get_stats(ca_pass, "alt_baro")
    }
    
    with open(OUT_JSON, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved Section 2.5 results to {OUT_JSON}")
    print(json.dumps(results, indent=2))
    return results

if __name__ == "__main__":
    run()
