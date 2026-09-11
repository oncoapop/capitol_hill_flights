"""
Section 2.3: Operational Categorisation and Vertical-Rate Validation
Categorises passes and records into Commercial arrivals, Commercial high, Business/private,
Light/float/helicopter, and Unclassifiable. Computes vertical rate distributions for validation.

Inputs: data/capitol_hill_passes.csv, data/capitol_hill_all_flights.csv, analysis/aircraft_classification.json
Output: analysis/results_section2_3.json
Date: 2026-09-10
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path

PASSES_FILE = Path("data/capitol_hill_passes.csv")
RAW_FILE = Path("data/capitol_hill_all_flights.csv")
MAPPING_FILE = Path("analysis/aircraft_classification.json")
OUT_JSON = Path("analysis/results_section2_3.json")

def run():
    print("Running Section 2.3: Operational Categorisation and Validation...")
    with open(MAPPING_FILE) as f:
        mapping = json.load(f)
        
    comm_types = set(mapping["commercial"])
    biz_types = set(mapping["business"])
    light_types = set(mapping["light_heli"])
    unclass_types = set(mapping["unclassifiable"])
    
    # 1. Evaluate on raw records
    df_raw = pd.read_csv(RAW_FILE)
    df_raw["type_code"] = df_raw["type_code"].fillna("MISSING")
    df_raw["alt"] = pd.to_numeric(df_raw["min_dist_alt_baro"], errors="coerce")
    
    n_total_records = len(df_raw)
    n_unclass_records = df_raw["type_code"].isin(unclass_types).sum()
    unclass_fraction = float(n_unclass_records / n_total_records)
    
    # 2. Evaluate on passes
    df_passes = pd.read_csv(PASSES_FILE)
    df_passes["type_code"] = df_passes["type_code"].fillna("MISSING")
    
    # Exclude passes where duration is too short (< 10 sec) or vs is null for vertical rate validation
    valid_vs = df_passes.dropna(subset=["vs_ft_min"]).copy()
    valid_vs = valid_vs[valid_vs["duration_sec"] >= 10]
    
    # Vertical rate by category
    ca_vs = valid_vs[valid_vs["type_code"].isin(comm_types) & (valid_vs["alt_baro"] < 10000)]["vs_ft_min"]
    ch_vs = valid_vs[valid_vs["type_code"].isin(comm_types) & (valid_vs["alt_baro"] >= 10000)]["vs_ft_min"]
    biz_vs = valid_vs[valid_vs["type_code"].isin(biz_types)]["vs_ft_min"]
    light_vs = valid_vs[valid_vs["type_code"].isin(light_types)]["vs_ft_min"]
    
    results = {
        "unclassifiable_records_count": int(n_unclass_records),
        "total_records": int(n_total_records),
        "unclassifiable_fraction": unclass_fraction,
        "unclassifiable_types": sorted(list(unclass_types)),
        "vertical_rate_validation": {
            "commercial_arrivals": {
                "median_fpm": float(ca_vs.median()),
                "mean_fpm": float(ca_vs.mean()),
                "pct_descending": float((ca_vs < 0).mean() * 100.0),
                "n": len(ca_vs)
            },
            "commercial_high": {
                "median_fpm": float(ch_vs.median()),
                "mean_fpm": float(ch_vs.mean()),
                "pct_climbing": float((ch_vs > 0).mean() * 100.0),
                "pct_descending": float((ch_vs < 0).mean() * 100.0),
                "n": len(ch_vs)
            },
            "business": {
                "median_fpm": float(biz_vs.median()),
                "mean_fpm": float(biz_vs.mean()),
                "pct_descending": float((biz_vs < 0).mean() * 100.0),
                "n": len(biz_vs)
            },
            "light": {
                "median_fpm": float(light_vs.median()),
                "mean_fpm": float(light_vs.mean()),
                "pct_level_or_desc": float((light_vs <= 0).mean() * 100.0),
                "n": len(light_vs)
            }
        }
    }
    
    with open(OUT_JSON, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved Section 2.3 results to {OUT_JSON}")
    print(json.dumps(results, indent=2))
    return results

if __name__ == "__main__":
    run()
