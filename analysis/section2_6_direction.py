"""
Section 2.6: Direction of Travel Analysis
Produces counts of overflights by category, era (pre/post VAMP), and heading band:
  E: 060–120°, W: 240–300°, N: 330–030°, S: 150–210°, Other.

Inputs: data/capitol_hill_all_flights.csv, analysis/aircraft_classification.json
Output: analysis/results_section2_6.json
Date: 2026-09-10
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path

RAW_FILE = Path("data/capitol_hill_all_flights.csv")
MAPPING_FILE = Path("analysis/aircraft_classification.json")
OUT_JSON = Path("analysis/results_section2_6.json")

def get_heading_band(track):
    if pd.isna(track):
        return "Other"
    track = float(track) % 360.0
    if 60.0 <= track <= 120.0:
        return "E"
    elif 240.0 <= track <= 300.0:
        return "W"
    elif track >= 330.0 or track <= 30.0:
        return "N"
    elif 150.0 <= track <= 210.0:
        return "S"
    else:
        return "Other"

def run():
    print("Running Section 2.6: Direction of Travel Analysis...")
    with open(MAPPING_FILE) as f:
        mapping = json.load(f)
    comm_types = set(mapping["commercial"])
    biz_types = set(mapping["business"])
    light_heli_types = set(mapping["light_heli"])
    
    df = pd.read_csv(RAW_FILE)
    df["type_code"] = df["type_code"].fillna("MISSING")
    df["alt"] = pd.to_numeric(df["min_dist_alt_baro"], errors="coerce")
    df["heading"] = df["min_dist_track"].apply(get_heading_band)
    df["era"] = np.where(df["date"] < "2025-11-27", "Before", "After")
    
    categories = {
        "Commercial arrivals": df[df["type_code"].isin(comm_types) & (df["alt"] < 10000)],
        "Business / private": df[df["type_code"].isin(biz_types)],
        "Control: light/float/heli": df[df["type_code"].isin(light_heli_types)],
        "Control: commercial >=10,000 ft": df[df["type_code"].isin(comm_types) & (df["alt"] >= 10000)]
    }
    
    headings = ["E", "W", "N", "S", "Other"]
    table_rows = []
    results_dict = {}
    
    for cat_name, sub in categories.items():
        results_dict[cat_name] = {}
        for era in ["Before", "After"]:
            era_sub = sub[sub["era"] == era]
            tot = len(era_sub)
            counts = {h: int((era_sub["heading"] == h).sum()) for h in headings}
            results_dict[cat_name][era] = {
                "total": tot,
                "counts": counts
            }
            row = [cat_name, era, tot] + [counts[h] for h in headings]
            table_rows.append(row)
            print(f"{cat_name:30s} | {era:6s} | Total: {tot:5d} | E: {counts['E']:4d} | W: {counts['W']:4d} | N: {counts['N']:4d} | S: {counts['S']:3d} | Other: {counts['Other']:3d}")
            
    results = {
        "heading_bands": {
            "E": "060-120 deg",
            "W": "240-300 deg",
            "N": "330-030 deg",
            "S": "150-210 deg",
            "Other": "remaining angles or missing"
        },
        "table": results_dict
    }
    
    with open(OUT_JSON, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved Section 2.6 results to {OUT_JSON}")
    return results

if __name__ == "__main__":
    run()
