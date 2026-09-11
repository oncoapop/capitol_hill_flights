"""
Section 2.4: Rate Ratios and Statistical Testing
Computes pass-based daily rates pre and post VAMP, rate ratios, 4,000 percentile bootstrap 95% CIs,
and two-sided Mann-Whitney U tests for all operational and control categories.

Inputs: data/capitol_hill_passes.csv, analysis/aircraft_classification.json
Output: analysis/results_section2_4.json
Date: 2026-09-10
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats

PASSES_FILE = Path("data/capitol_hill_passes.csv")
MAPPING_FILE = Path("analysis/aircraft_classification.json")
OUT_JSON = Path("analysis/results_section2_4.json")

def run():
    print("Running Section 2.4: Rate Ratios and Statistical Testing...")
    with open(MAPPING_FILE) as f:
        mapping = json.load(f)
        
    comm_types = set(mapping["commercial"])
    biz_types = set(mapping["business"])
    light_types = set(mapping["light_heli"])
    heli_types = {'R44', 'S76', 'B06', 'AS50', 'A139', 'EC35', 'EC20', 'B407', 'B412', 'B429', 'HU50', 'R22', 'R66', 'S92', 'EC45', 'AS55', 'B212', 'A109', 'BK17', 'H500', 'B05', 'EC30', 'A169', 'EH10', 'B505', 'H60', 'UH1'}
    
    df_passes = pd.read_csv(PASSES_FILE)
    
    dates_with_data = sorted(df_passes["date"].unique())
    pre_dates = [d for d in dates_with_data if d < "2025-11-27"]
    post_dates = [d for d in dates_with_data if d >= "2025-11-27"]
    n_pre = len(pre_dates)
    n_post = len(post_dates)
    
    categories = {
        "commercial_arrivals_500m": df_passes[df_passes["type_code"].isin(comm_types) & (df_passes["alt_baro"] < 10000) & (df_passes["dist_km"] <= 0.5)],
        "commercial_arrivals_1500m": df_passes[df_passes["type_code"].isin(comm_types) & (df_passes["alt_baro"] < 10000)],
        "business_private": df_passes[df_passes["type_code"].isin(biz_types)],
        "all_aircraft_1500m": df_passes,
        "control_light_fixed_wing_floatplane": df_passes[df_passes["type_code"].isin(light_types) & (~df_passes["type_code"].isin(heli_types))],
        "control_commercial_high": df_passes[df_passes["type_code"].isin(comm_types) & (df_passes["alt_baro"] >= 10000)]
    }
    
    results = {
        "denominators": {
            "pre_days_with_data": n_pre,
            "post_days_with_data": n_post
        },
        "bootstrap_method": "percentile",
        "bootstrap_resamples": 4000,
        "categories": {}
    }
    
    np.random.seed(42)
    
    for cat_name, sub_df in categories.items():
        daily_pre = sub_df[sub_df["date"] < "2025-11-27"].groupby("date").size().reindex(pre_dates, fill_value=0).values
        daily_post = sub_df[sub_df["date"] >= "2025-11-27"].groupby("date").size().reindex(post_dates, fill_value=0).values
        
        m_pre = float(np.mean(daily_pre))
        m_post = float(np.mean(daily_post))
        rr = float(m_post / m_pre) if m_pre > 0 else np.nan
        
        # Mann-Whitney U test (two-sided)
        u_stat, p_val = stats.mannwhitneyu(daily_post, daily_pre, alternative="two-sided")
        
        # 4,000 percentile bootstrap resamples on calendar days
        boot_rr = []
        for _ in range(4000):
            b_pre = np.random.choice(daily_pre, size=n_pre, replace=True)
            b_post = np.random.choice(daily_post, size=n_post, replace=True)
            mp = np.mean(b_pre)
            mpo = np.mean(b_post)
            if mp > 0:
                boot_rr.append(mpo / mp)
                
        ci_lo = float(np.percentile(boot_rr, 2.5))
        ci_hi = float(np.percentile(boot_rr, 97.5))
        
        results["categories"][cat_name] = {
            "pre_mean": m_pre,
            "post_mean": m_post,
            "rate_ratio": rr,
            "ci_95_percentile": [ci_lo, ci_hi],
            "mann_whitney_u": float(u_stat),
            "p_value": float(p_val)
        }
        print(f"{cat_name:35s} | Pre: {m_pre:5.2f} | Post: {m_post:5.2f} | RR: {rr:4.2f} ({ci_lo:.2f}–{ci_hi:.2f}) | p={p_val:.2e}")
        
    with open(OUT_JSON, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved Section 2.4 results to {OUT_JSON}")
    return results

if __name__ == "__main__":
    run()
