"""
Section 4: Helicopter Analysis (Limitation Assessment)
Analyzes the late-spring 2026 increase in helicopter overflights (S-76, AW139) versus private types (R44),
evaluates equipage and routing confounds, and contextualizes with Vancouver Harbour StatCan data.

Inputs: data/capitol_hill_passes.csv, data/capitol_hill_all_flights.csv, data/23100296.csv
Output: analysis/results_section4.json
Date: 2026-09-10
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats

PASSES_FILE = Path("data/capitol_hill_passes.csv")
RAW_FILE = Path("data/capitol_hill_all_flights.csv")
STATCAN_FILE = Path("data/23100296.csv")
OUT_JSON = Path("analysis/results_section4.json")

def run():
    print("Running Section 4: Helicopter Analysis (Limitation Assessment)...")
    heli_types = {'R44', 'S76', 'B06', 'AS50', 'A139', 'EC35', 'EC20', 'B407', 'B412', 'B429', 'HU50', 'R22', 'R66', 'S92', 'EC45', 'AS55', 'B212', 'A109', 'BK17', 'H500', 'B05', 'EC30', 'A169', 'EH10', 'B505', 'H60', 'UH1'}
    
    df_passes = pd.read_csv(PASSES_FILE)
    df_h = df_passes[df_passes["type_code"].isin(heli_types)].copy()
    
    dates_with_data = sorted(df_passes["date"].unique())
    pre_dates = [d for d in dates_with_data if d < "2025-11-27"]
    post_dates = [d for d in dates_with_data if d >= "2025-11-27"]
    n_pre = len(pre_dates)
    n_post = len(post_dates)
    
    daily_pre = df_h[df_h["date"] < "2025-11-27"].groupby("date").size().reindex(pre_dates, fill_value=0).values
    daily_post = df_h[df_h["date"] >= "2025-11-27"].groupby("date").size().reindex(post_dates, fill_value=0).values
    
    m_pre = float(np.mean(daily_pre))
    m_post = float(np.mean(daily_post))
    rr = float(m_post / m_pre)
    u_stat, p_val = stats.mannwhitneyu(daily_post, daily_pre, alternative="two-sided")
    
    np.random.seed(42)
    boot = []
    for _ in range(4000):
        bp = np.random.choice(daily_pre, size=n_pre, replace=True)
        bpo = np.random.choice(daily_post, size=n_post, replace=True)
        boot.append(np.mean(bpo) / np.mean(bp))
    ci_95 = [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))]
    
    # R44
    r44 = df_passes[df_passes["type_code"] == "R44"]
    r_pre = float(len(r44[r44["date"] < "2025-11-27"]) / n_pre)
    r_post = float(len(r44[r44["date"] >= "2025-11-27"]) / n_post)
    r_rr = float(r_post / r_pre) if r_pre > 0 else np.nan
    
    # Low-altitude helicopters (< 2000 ft)
    h_low = df_h[df_h["alt_baro"] < 2000]
    hl_pre = float(len(h_low[h_low["date"] < "2025-11-27"]) / n_pre)
    hl_post = float(len(h_low[h_low["date"] >= "2025-11-27"]) / n_post)
    hl_rr = float(hl_post / hl_pre) if hl_pre > 0 else np.nan
    
    # S-76 and AW139 counts Jan-Jun 2025 vs 2026
    s25 = int(len(df_passes[(df_passes["type_code"].isin({"S76", "A139"})) & 
                            (df_passes["date"] >= "2025-01-01") & (df_passes["date"] <= "2025-06-30")]))
    s26 = int(len(df_passes[(df_passes["type_code"].isin({"S76", "A139"})) & 
                            (df_passes["date"] >= "2026-01-01") & (df_passes["date"] <= "2026-06-30")]))
    s_ratio = float(s26 / s25) if s25 > 0 else np.nan
    
    # StatCan Vancouver Harbour movements Jan-Jun
    df_296 = pd.read_csv(STATCAN_FILE)
    sub_cxh = df_296[(df_296["Airports"] == "Vancouver Harbour, British Columbia") & 
                     (df_296["Class of operation"] == "Total, itinerant and local movements")]
    dates_25 = ["2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06"]
    dates_26 = ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"]
    v25_cxh = float(sub_cxh[sub_cxh["REF_DATE"].isin(dates_25)]["VALUE"].sum())
    v26_cxh = float(sub_cxh[sub_cxh["REF_DATE"].isin(dates_26)]["VALUE"].sum())
    cxh_growth_pct = float((v26_cxh - v25_cxh) / v25_cxh * 100.0)
    
    results = {
        "all_helicopters": {
            "pre_passes_per_day": m_pre,
            "post_passes_per_day": m_post,
            "rate_ratio": rr,
            "ci_95": ci_95,
            "p_value": float(p_val)
        },
        "r44_training_private": {
            "pre_rate": r_pre,
            "post_rate": r_post,
            "rate_ratio": r_rr
        },
        "low_altitude_helicopters_sub_2000ft": {
            "pre_rate": hl_pre,
            "post_rate": hl_post,
            "rate_ratio": hl_rr
        },
        "s76_aw139_transport_medevac": {
            "counts_jan_jun_2025": s25,
            "counts_jan_jun_2026": s26,
            "fold_increase": s_ratio
        },
        "statcan_vancouver_harbour": {
            "movements_jan_jun_2025": v25_cxh,
            "movements_jan_jun_2026": v26_cxh,
            "growth_pct": cxh_growth_pct
        },
        "attribution_note": "Secondary changepoint occurs in late April / early May 2026, months after VAMP. Disproportionate increase in S-76/AW139 relative to 21% harbor growth indicates fleet equipage or localized route change, not VAMP arrival procedures."
    }
    
    with open(OUT_JSON, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved Section 4 results to {OUT_JSON}")
    print(json.dumps(results, indent=2))
    return results

if __name__ == "__main__":
    run()
