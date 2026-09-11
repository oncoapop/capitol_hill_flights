"""
Section 2.9: External Validation against Statistics Canada
Extracts monthly movement counts from StatCan Tables 23-10-0296 and 23-10-0303,
compares matched Jan–Jun 2025 vs Jan–Jun 2026 ratios against ADS-B Capitol Hill observations.

Inputs: data/23100296.csv, data/23100303.csv, data/capitol_hill_all_flights.csv, analysis/aircraft_classification.json
Output: analysis/results_section2_9.json
Date: 2026-09-10
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path

FILE_296 = Path("data/23100296.csv")
FILE_303 = Path("data/23100303.csv")
RAW_FILE = Path("data/capitol_hill_all_flights.csv")
MAPPING_FILE = Path("analysis/aircraft_classification.json")
OUT_JSON = Path("analysis/results_section2_9.json")

def run():
    print("Running Section 2.9: External Validation against Statistics Canada...")
    
    # 1. StatCan Table 23-10-0296 (Airports)
    df_296 = pd.read_csv(FILE_296)
    sub_296 = df_296[df_296["Class of operation"] == "Total, itinerant and local movements"]
    
    dates_25 = ["2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06"]
    dates_26 = ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"]
    
    airports = {
        "YVR": "Vancouver International, British Columbia",
        "Boundary_Bay": "Boundary Bay, British Columbia",
        "Pitt_Meadows": "Pitt Meadows, British Columbia",
        "Langley": "Langley, British Columbia",
        "Vancouver_Harbour": "Vancouver Harbour, British Columbia"
    }
    
    statcan_ratios = {}
    
    for key, name in airports.items():
        v25 = float(sub_296[(sub_296["Airports"] == name) & (sub_296["REF_DATE"].isin(dates_25))]["VALUE"].sum())
        v26 = float(sub_296[(sub_296["Airports"] == name) & (sub_296["REF_DATE"].isin(dates_26))]["VALUE"].sum())
        statcan_ratios[key] = {
            "movements_2025_jan_jun": v25,
            "movements_2026_jan_jun": v26,
            "ratio": float(v26 / v25) if v25 > 0 else np.nan
        }
        
    # GA Combined
    ga_names = [airports["Boundary_Bay"], airports["Pitt_Meadows"], airports["Langley"]]
    v25_ga = float(sub_296[(sub_296["Airports"].isin(ga_names)) & (sub_296["REF_DATE"].isin(dates_25))]["VALUE"].sum())
    v26_ga = float(sub_296[(sub_296["Airports"].isin(ga_names)) & (sub_296["REF_DATE"].isin(dates_26))]["VALUE"].sum())
    statcan_ratios["GA_combined"] = {
        "movements_2025_jan_jun": v25_ga,
        "movements_2026_jan_jun": v26_ga,
        "ratio": float(v26_ga / v25_ga) if v25_ga > 0 else np.nan
    }
    
    # 2. StatCan Table 23-10-0303 (BC All Airports)
    df_303 = pd.read_csv(FILE_303)
    sub_303 = df_303[(df_303["GEO"].str.contains("British Columbia", na=False)) & 
                     (df_303["Class of operation"] == "Total, itinerant and local movements")]
    v25_bc = float(sub_303[sub_303["REF_DATE"].isin(dates_25)]["VALUE"].sum())
    v26_bc = float(sub_303[sub_303["REF_DATE"].isin(dates_26)]["VALUE"].sum())
    statcan_ratios["BC_all_airports"] = {
        "movements_2025_jan_jun": v25_bc,
        "movements_2026_jan_jun": v26_bc,
        "ratio": float(v26_bc / v25_bc) if v25_bc > 0 else np.nan
    }
    
    # 3. ADS-B Capitol Hill matched Jan-Jun
    with open(MAPPING_FILE) as f:
        mapping = json.load(f)
    comm_types = set(mapping["commercial"])
    light_types = set(mapping["light_heli"])
    heli_types = {'R44', 'S76', 'B06', 'AS50', 'A139', 'EC35', 'EC20', 'B407', 'B412', 'B429', 'HU50', 'R22', 'R66', 'S92', 'EC45', 'AS55', 'B212', 'A109', 'BK17', 'H500', 'B05', 'EC30', 'A169', 'EH10', 'B505', 'H60', 'UH1'}
    
    df_raw = pd.read_csv(RAW_FILE)
    df_raw["alt"] = pd.to_numeric(df_raw["min_dist_alt_baro"], errors="coerce")
    
    raw_25 = df_raw[(df_raw["date"] >= "2025-01-01") & (df_raw["date"] <= "2025-06-30")]
    raw_26 = df_raw[(df_raw["date"] >= "2026-01-01") & (df_raw["date"] <= "2026-06-30")]
    d25 = len(raw_25["date"].unique())
    d26 = len(raw_26["date"].unique())
    
    ca_25 = len(raw_25[raw_25["type_code"].isin(comm_types) & (raw_25["alt"] < 10000)]) / d25
    ca_26 = len(raw_26[raw_26["type_code"].isin(comm_types) & (raw_26["alt"] < 10000)]) / d26
    adsb_ca_ratio = float(ca_26 / ca_25)
    
    lg_25 = len(raw_25[raw_25["type_code"].isin(light_types) & (~raw_25["type_code"].isin(heli_types))]) / d25
    lg_26 = len(raw_26[raw_26["type_code"].isin(light_types) & (~raw_26["type_code"].isin(heli_types))]) / d26
    adsb_lg_ratio = float(lg_26 / lg_25)
    
    results = {
        "window": "Jan-Jun 2025 vs Jan-Jun 2026",
        "statcan": statcan_ratios,
        "adsb_capitol_hill": {
            "commercial_arrivals": {
                "daily_rate_2025": ca_25,
                "daily_rate_2026": ca_26,
                "ratio": adsb_ca_ratio
            },
            "light_fixed_wing_ga": {
                "daily_rate_2025": lg_25,
                "daily_rate_2026": lg_26,
                "ratio": adsb_lg_ratio
            }
        }
    }
    
    with open(OUT_JSON, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved Section 2.9 results to {OUT_JSON}")
    print(json.dumps(results, indent=2))
    return results

if __name__ == "__main__":
    run()
