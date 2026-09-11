"""
Section 2.1: Coverage and Unit of Observation
Rebuilds coverage statistics, identifies absent dates, and reconstructs discrete passes
from trajectory timestamps with threshold sensitivity and gap distribution analysis.

Inputs: data/capitol_hill_all_flights.csv, data/daily_flight_counts_complete_months.csv
Output: analysis/results_section2_1.json, data/capitol_hill_passes.csv
Date: 2026-09-10
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path

DATA_FILE = Path("data/capitol_hill_all_flights.csv")
DAILY_FILE = Path("data/daily_flight_counts_complete_months.csv")
OUT_JSON = Path("analysis/results_section2_1.json")
OUT_PASSES = Path("data/capitol_hill_passes.csv")

def run():
    print("Running Section 2.1: Coverage and Unit of Observation...")
    df = pd.read_csv(DATA_FILE)
    
    total_records = len(df)
    unique_icaos = df["icao"].nunique()
    unique_date_icao = df.drop_duplicates(subset=["date", "icao"]).shape[0]
    is_date_icao_unique = (total_records == unique_date_icao)
    
    # Dates
    dates_with_data = sorted(df["date"].unique().tolist())
    n_days_with_data = len(dates_with_data)
    
    all_calendar_dates = pd.date_range("2025-01-01", "2026-08-31").strftime("%Y-%m-%d").tolist()
    n_calendar_days = len(all_calendar_dates)
    
    absent_dates = sorted(list(set(all_calendar_dates) - set(dates_with_data)))
    n_absent_days = len(absent_dates)
    
    # Pre / Post changepoint days (27 Nov 2025)
    pre_dates_with_data = [d for d in dates_with_data if d < "2025-11-27"]
    post_dates_with_data = [d for d in dates_with_data if d >= "2025-11-27"]
    n_pre_days_data = len(pre_dates_with_data)
    n_post_days_data = len(post_dates_with_data)
    
    pre_calendar = [d for d in all_calendar_dates if d < "2025-11-27"]
    post_calendar = [d for d in all_calendar_dates if d >= "2025-11-27"]
    n_pre_calendar = len(pre_calendar)
    n_post_calendar = len(post_calendar)
    
    # Pass clustering and gap distribution
    all_gaps = []
    passes_5min = 0
    passes_10min = 0
    passes_15min = 0
    passes_30min = 0
    
    extracted_passes = []
    
    for idx, row in df.iterrows():
        pts_raw = row["matched_points_json"]
        if not isinstance(pts_raw, str):
            continue
        pts = json.loads(pts_raw)
        if not pts:
            continue
        pts = sorted(pts, key=lambda x: x["timestamp"])
        
        # Gaps
        ts = [p["timestamp"] for p in pts]
        if len(ts) > 1:
            gaps = np.diff(ts).tolist()
            all_gaps.extend(gaps)
        else:
            gaps = []
            
        passes_5min += 1 + sum(g > 300 for g in gaps)
        passes_10min += 1 + sum(g > 600 for g in gaps)
        passes_15min += 1 + sum(g > 900 for g in gaps)
        passes_30min += 1 + sum(g > 1800 for g in gaps)
        
        # Cluster at 10 min (600 s) for primary pass dataset
        pass_clusters = []
        curr = [pts[0]]
        for p in pts[1:]:
            if p["timestamp"] - curr[-1]["timestamp"] > 600:
                pass_clusters.append(curr)
                curr = [p]
            else:
                curr.append(p)
        if curr:
            pass_clusters.append(curr)
            
        for pass_idx, p_pts in enumerate(pass_clusters):
            # CPA point: min dist_km
            cpa_pt = min(p_pts, key=lambda x: x["dist_km"])
            
            # Vertical rate from altitude sequence
            vs = np.nan
            if len(p_pts) >= 2:
                dt_min = (p_pts[-1]["timestamp"] - p_pts[0]["timestamp"]) / 60.0
                if dt_min > 0:
                    try:
                        a0 = float(p_pts[0]["alt_baro"])
                        a1 = float(p_pts[-1]["alt_baro"])
                        vs = (a1 - a0) / dt_min
                    except (ValueError, TypeError):
                        pass
                        
            # Safe altitude conversion
            alt_baro = cpa_pt.get("alt_baro")
            try:
                alt_baro = float(alt_baro)
            except (ValueError, TypeError):
                alt_baro = np.nan
                
            extracted_passes.append({
                "flight_id": row["id"],
                "date": row["date"],
                "icao": row["icao"],
                "type_code": row["type_code"] if pd.notna(row["type_code"]) else "MISSING",
                "pass_idx": pass_idx,
                "cpa_timestamp": cpa_pt["timestamp"],
                "dist_km": cpa_pt["dist_km"],
                "alt_baro": alt_baro,
                "alt_geom": cpa_pt.get("alt_geom", np.nan),
                "track": cpa_pt.get("track", np.nan),
                "gs": cpa_pt.get("gs", np.nan),
                "lat": cpa_pt.get("lat", np.nan),
                "lon": cpa_pt.get("lon", np.nan),
                "num_points": len(p_pts),
                "duration_sec": p_pts[-1]["timestamp"] - p_pts[0]["timestamp"],
                "vs_ft_min": vs
            })
            
    all_gaps = np.array(all_gaps)
    median_gap = float(np.median(all_gaps))
    pct_gaps_le_60s = float(np.mean(all_gaps <= 60) * 100.0)
    inflation_factor = float(passes_10min / total_records)
    
    # Save extracted passes
    passes_df = pd.DataFrame(extracted_passes)
    passes_df.to_csv(OUT_PASSES, index=False)
    print(f"Saved {len(passes_df)} discrete passes to {OUT_PASSES}")
    
    # Inflation factor by era
    pre_records = len(df[df["date"] < "2025-11-27"])
    post_records = len(df[df["date"] >= "2025-11-27"])
    pre_passes = len(passes_df[passes_df["date"] < "2025-11-27"])
    post_passes = len(passes_df[passes_df["date"] >= "2025-11-27"])
    
    results = {
        "total_records": total_records,
        "unique_icaos": unique_icaos,
        "is_date_icao_unique": is_date_icao_unique,
        "calendar_days_total": n_calendar_days,
        "days_with_data": n_days_with_data,
        "absent_days_count": n_absent_days,
        "absent_dates": absent_dates,
        "pre_changepoint_days_with_data": n_pre_days_data,
        "post_changepoint_days_with_data": n_post_days_data,
        "pre_changepoint_calendar_days": n_pre_calendar,
        "post_changepoint_calendar_days": n_post_calendar,
        "threshold_sensitivity": {
            "passes_5min": passes_5min,
            "passes_10min": passes_10min,
            "passes_15min": passes_15min,
            "passes_30min": passes_30min
        },
        "primary_passes_10min": passes_10min,
        "inflation_factor_overall": inflation_factor,
        "pre_records": pre_records,
        "post_records": post_records,
        "pre_passes": pre_passes,
        "post_passes": post_passes,
        "inflation_factor_pre": float(pre_passes / pre_records),
        "inflation_factor_post": float(post_passes / post_records),
        "gap_distribution": {
            "median_gap_sec": median_gap,
            "pct_gaps_le_60s": pct_gaps_le_60s
        }
    }
    
    with open(OUT_JSON, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved results to {OUT_JSON}")
    print(json.dumps(results, indent=2))
    return results

if __name__ == "__main__":
    run()
