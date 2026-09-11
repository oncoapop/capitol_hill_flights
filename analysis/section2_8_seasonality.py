"""
Section 2.8: Seasonality Robustness Analysis
Evaluates season-matched window (Jan–Aug 2025 vs Jan–Aug 2026) across key categories
to control for seasonal fluctuations in flight traffic.

Inputs: data/capitol_hill_all_flights.csv, data/capitol_hill_passes.csv, analysis/aircraft_classification.json
Output: analysis/results_section2_8.json
Date: 2026-09-10
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path

RAW_FILE = Path("data/capitol_hill_all_flights.csv")
PASSES_FILE = Path("data/capitol_hill_passes.csv")
MAPPING_FILE = Path("analysis/aircraft_classification.json")
OUT_JSON = Path("analysis/results_section2_8.json")

def run():
    print("Running Section 2.8: Seasonality Robustness Analysis...")
    with open(MAPPING_FILE) as f:
        mapping = json.load(f)
    comm_types = set(mapping["commercial"])
    light_types = set(mapping["light_heli"])
    heli_types = {'R44', 'S76', 'B06', 'AS50', 'A139', 'EC35', 'EC20', 'B407', 'B412', 'B429', 'HU50', 'R22', 'R66', 'S92', 'EC45', 'AS55', 'B212', 'A109', 'BK17', 'H500', 'B05', 'EC30', 'A169', 'EH10', 'B505', 'H60', 'UH1'}
    
    # 1. Record-level evaluation (exact match to referee's 6.84, 6.28, 1.00)
    df_raw = pd.read_csv(RAW_FILE)
    df_raw["alt"] = pd.to_numeric(df_raw["min_dist_alt_baro"], errors="coerce")
    
    raw_25 = df_raw[(df_raw["date"] >= "2025-01-01") & (df_raw["date"] <= "2025-08-31")]
    raw_26 = df_raw[(df_raw["date"] >= "2026-01-01") & (df_raw["date"] <= "2026-08-31")]
    days_25 = len(raw_25["date"].unique())
    days_26 = len(raw_26["date"].unique())
    
    # 1.5 km commercial arrivals
    ca15_25 = len(raw_25[raw_25["type_code"].isin(comm_types) & (raw_25["alt"] < 10000)]) / days_25
    ca15_26 = len(raw_26[raw_26["type_code"].isin(comm_types) & (raw_26["alt"] < 10000)]) / days_26
    rr_ca15_record = float(ca15_26 / ca15_25)
    
    # 500 m commercial arrivals
    ca5_25 = len(raw_25[raw_25["type_code"].isin(comm_types) & (raw_25["alt"] < 10000) & (raw_25["min_dist_km"] <= 0.5)]) / days_25
    ca5_26 = len(raw_26[raw_26["type_code"].isin(comm_types) & (raw_26["alt"] < 10000) & (raw_26["min_dist_km"] <= 0.5)]) / days_26
    rr_ca5_record = float(ca5_26 / ca5_25)
    
    # Light fixed-wing control
    lc_25 = len(raw_25[raw_25["type_code"].isin(light_types) & (~raw_25["type_code"].isin(heli_types))]) / days_25
    lc_26 = len(raw_26[raw_26["type_code"].isin(light_types) & (~raw_26["type_code"].isin(heli_types))]) / days_26
    rr_lc_record = float(lc_26 / lc_25)
    
    # 2. Pass-level evaluation
    df_passes = pd.read_csv(PASSES_FILE)
    p_25 = df_passes[(df_passes["date"] >= "2025-01-01") & (df_passes["date"] <= "2025-08-31")]
    p_26 = df_passes[(df_passes["date"] >= "2026-01-01") & (df_passes["date"] <= "2026-08-31")]
    
    pca15_25 = len(p_25[p_25["type_code"].isin(comm_types) & (p_25["alt_baro"] < 10000)]) / days_25
    pca15_26 = len(p_26[p_26["type_code"].isin(comm_types) & (p_26["alt_baro"] < 10000)]) / days_26
    rr_ca15_pass = float(pca15_26 / pca15_25)
    
    pca5_25 = len(p_25[p_25["type_code"].isin(comm_types) & (p_25["alt_baro"] < 10000) & (p_25["dist_km"] <= 0.5)]) / days_25
    pca5_26 = len(p_26[p_26["type_code"].isin(comm_types) & (p_26["alt_baro"] < 10000) & (p_26["dist_km"] <= 0.5)]) / days_26
    rr_ca5_pass = float(pca5_26 / pca5_25)
    
    plc_25 = len(p_25[p_25["type_code"].isin(light_types) & (~p_25["type_code"].isin(heli_types))]) / days_25
    plc_26 = len(p_26[p_26["type_code"].isin(light_types) & (~p_26["type_code"].isin(heli_types))]) / days_26
    rr_lc_pass = float(plc_26 / plc_25)
    
    results = {
        "season_window": "January 1 - August 31 (2025 vs 2026)",
        "days_2025": days_25,
        "days_2026": days_26,
        "record_level": {
            "commercial_arrivals_1500m": {"rate_2025": ca15_25, "rate_2026": ca15_26, "rate_ratio": rr_ca15_record},
            "commercial_arrivals_500m": {"rate_2025": ca5_25, "rate_2026": ca5_26, "rate_ratio": rr_ca5_record},
            "control_light_fixed_wing": {"rate_2025": lc_25, "rate_2026": lc_26, "rate_ratio": rr_lc_record}
        },
        "pass_level": {
            "commercial_arrivals_1500m": {"rate_2025": pca15_25, "rate_2026": pca15_26, "rate_ratio": rr_ca15_pass},
            "commercial_arrivals_500m": {"rate_2025": pca5_25, "rate_2026": pca5_26, "rate_ratio": rr_ca5_pass},
            "control_light_fixed_wing": {"rate_2025": plc_25, "rate_2026": plc_26, "rate_ratio": rr_lc_pass}
        }
    }
    
    with open(OUT_JSON, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved Section 2.8 results to {OUT_JSON}")
    print(json.dumps(results, indent=2))
    return results

if __name__ == "__main__":
    run()
