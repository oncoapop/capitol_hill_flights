"""
Section 2.2: Algorithmic Changepoint Detection
Runs exhaustive least-squares single-changepoint search and ruptures PELT/Binseg on daily series.
Performs parametric bootstrap for changepoint uncertainty.
Detects secondary changepoint in helicopter and S-76/AW139 series.

Inputs: data/capitol_hill_passes.csv
Output: analysis/results_section2_2.json
Date: 2026-09-10
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path
import ruptures as rpt

PASSES_FILE = Path("data/capitol_hill_passes.csv")
OUT_JSON = Path("analysis/results_section2_2.json")

def find_single_changepoint_ls(series):
    """Exhaustive least-squares single changepoint search."""
    y = np.array(series, dtype=float)
    n = len(y)
    best_cost = np.inf
    best_idx = None
    
    for k in range(5, n - 5):
        y1 = y[:k]
        y2 = y[k:]
        cost = np.sum((y1 - np.mean(y1))**2) + np.sum((y2 - np.mean(y2))**2)
        if cost < best_cost:
            best_cost = cost
            best_idx = k
    return best_idx, best_cost

def run():
    print("Running Section 2.2: Algorithmic Changepoint Detection...")
    df_passes = pd.read_csv(PASSES_FILE)
    
    # 1. Total daily pass counts
    daily_all = df_passes.groupby("date").size().reset_index(name="count")
    daily_all = daily_all.sort_values("date").reset_index(drop=True)
    
    dates = daily_all["date"].values
    counts = daily_all["count"].values
    
    best_k, best_cost = find_single_changepoint_ls(counts)
    detected_date = str(dates[best_k])
    print(f"Overall changepoint detected: {detected_date} (index {best_k})")
    
    # Cross-check with ruptures Binseg and PELT
    algo_binseg = rpt.Binseg(model="l2").fit(counts)
    binseg_res = algo_binseg.predict(n_bkps=1)
    binseg_date = str(dates[binseg_res[0]])
    print(f"Binseg changepoint: {binseg_date}")
    
    algo_pelt = rpt.Pelt(model="l2", min_size=5).fit(counts)
    pelt_res = algo_pelt.predict(pen=np.log(len(counts)) * np.var(counts))
    pelt_dates = [str(dates[idx-1]) for idx in pelt_res if idx < len(dates)]
    print(f"PELT changepoint(s): {pelt_dates}")
    
    # Parametric bootstrap on overall series (4,000 resamples)
    y1 = counts[:best_k]
    y2 = counts[best_k:]
    mu1, std1 = np.mean(y1), np.std(y1, ddof=1)
    mu2, std2 = np.mean(y2), np.std(y2, ddof=1)
    
    np.random.seed(42)
    boot_indices = []
    n_boot = 4000
    for _ in range(n_boot):
        sim1 = np.random.normal(mu1, std1, len(y1))
        sim2 = np.random.normal(mu2, std2, len(y2))
        sim_y = np.clip(np.concatenate([sim1, sim2]), 0, None)
        k_sim, _ = find_single_changepoint_ls(sim_y)
        boot_indices.append(k_sim)
        
    boot_indices = np.array(boot_indices)
    pct_on_detected = float(np.mean(boot_indices == best_k) * 100.0)
    lo_idx = int(np.percentile(boot_indices, 2.5))
    hi_idx = int(np.percentile(boot_indices, 97.5))
    ci_95 = [str(dates[lo_idx]), str(dates[hi_idx])]
    print(f"Bootstrap exact match: {pct_on_detected:.2f}%, 95% CI: {ci_95}")
    
    # 2. Helicopter subset changepoint (look in 2026)
    heli_types = {'R44', 'S76', 'B06', 'AS50', 'A139', 'EC35', 'EC20', 'B407', 'B412', 'B429', 'HU50', 'R22', 'R66', 'S92', 'EC45', 'AS55', 'B212', 'A109', 'BK17', 'H500', 'B05', 'EC30', 'A169', 'EH10', 'B505', 'H60', 'UH1'}
    df_heli = df_passes[df_passes["type_code"].isin(heli_types)]
    daily_heli = df_heli.groupby("date").size().reindex(dates, fill_value=0).reset_index()
    daily_heli.columns = ["date", "count"]
    
    # Focus search on post-Nov 2025 window or overall
    # Let's search across all dates
    h_counts = daily_heli["count"].values
    best_k_h, _ = find_single_changepoint_ls(h_counts)
    heli_cp_date = str(dates[best_k_h])
    print(f"Helicopter changepoint: {heli_cp_date}")
    
    # 3. S-76 / AW139 subset changepoint
    df_s76_139 = df_passes[df_passes["type_code"].isin({"S76", "A139"})]
    daily_s76_139 = df_s76_139.groupby("date").size().reindex(dates, fill_value=0).reset_index()
    daily_s76_139.columns = ["date", "count"]
    
    s_counts = daily_s76_139["count"].values
    best_k_s, _ = find_single_changepoint_ls(s_counts)
    s76_cp_date = str(dates[best_k_s])
    print(f"S-76 / AW139 changepoint: {s76_cp_date}")
    
    results = {
        "overall_changepoint_ls": detected_date,
        "overall_changepoint_binseg": binseg_date,
        "overall_changepoint_pelt": pelt_dates,
        "airac_cycle": "2513",
        "airac_cycle_days": 28,
        "airac_effective_date": "2025-11-27",
        "parametric_bootstrap": {
            "resamples": n_boot,
            "pct_exact_match_detected_date": pct_on_detected,
            "ci_95": ci_95
        },
        "helicopter_changepoint": heli_cp_date,
        "s76_aw139_changepoint": s76_cp_date
    }
    
    with open(OUT_JSON, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved Section 2.2 results to {OUT_JSON}")
    return results

if __name__ == "__main__":
    run()
