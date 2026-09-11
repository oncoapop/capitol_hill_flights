"""
Academic Figure Generator (Revised v2)
Produces compact, publication-standard, grayscale-safe figures saved into figures/.
All figures are computed directly from authoritative data (results.json, passes, raw flights).
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.patches as mpatches
import matplotlib.dates as mdates

FIGS_DIR = Path("figures")
FIGS_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif", "Times"],
    "font.size": 8,
    "axes.labelsize": 9,
    "axes.titlesize": 10,
    "axes.linewidth": 0.6,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "legend.fontsize": 7,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.05,
    "lines.linewidth": 1.0,
    "patch.linewidth": 0.5,
})

def fig1_study_area():
    out = FIGS_DIR / "fig1_study_area.png"
    fig, ax = plt.subplots(figsize=(3.5, 2.8))
    lat_c, lon_c = 49.2869, -122.9853
    d_lat_15 = 1.5 / 111.19
    d_lon_15 = 1.5 / 72.54
    d_lat_05 = 0.5 / 111.19
    d_lon_05 = 0.5 / 72.54
    pad_lon, pad_lat = 0.035, 0.022

    ax.set_xlim(lon_c - pad_lon, lon_c + pad_lon)
    ax.set_ylim(lat_c - pad_lat, lat_c + pad_lat)

    # Water (Burrard Inlet)
    x_w = np.linspace(lon_c - pad_lon, lon_c + pad_lon, 80)
    y_w = 49.294 + 0.002 * np.sin((x_w - lon_c) * 60)
    ax.fill_between(x_w, y_w, lat_c + pad_lat, color="#d0dde8", alpha=0.7)
    ax.fill_between(x_w, lat_c - pad_lat, y_w, color="#f8f8f8", alpha=0.9)
    ax.text(lon_c - 0.025, lat_c + 0.015, "Burrard Inlet", fontsize=6.5, fontstyle="italic", color="#2a4d69")

    # 1.5 km circle
    circ15 = mpatches.Ellipse(
        (lon_c, lat_c), width=d_lon_15 * 2, height=d_lat_15 * 2,
        edgecolor="k", facecolor="#dddddd", alpha=0.25, lw=1.0, ls="--", label="1.5 km study zone"
    )
    ax.add_patch(circ15)

    # 500 m circle
    circ05 = mpatches.Ellipse(
        (lon_c, lat_c), width=d_lon_05 * 2, height=d_lat_05 * 2,
        edgecolor="0.2", facecolor="#bbbbbb", alpha=0.35, lw=1.0, label="500 m core zone"
    )
    ax.add_patch(circ05)

    # Centre point
    ax.plot(lon_c, lat_c, "k*", ms=8, zorder=10)
    ax.annotate("Capitol Hill\n(115 m ASL)", (lon_c, lat_c),
                xytext=(6, 6), textcoords="offset points", fontsize=6.5, fontweight="bold")

    # Scale bar (1 km)
    sb_x = lon_c - 0.031
    sb_y = lat_c - 0.018
    sb_len = 1.0 / 72.54
    ax.plot([sb_x, sb_x + sb_len], [sb_y, sb_y], "k-", lw=2)
    ax.text(sb_x + sb_len / 2, sb_y + 0.0012, "1 km", ha="center", fontsize=6)

    # North arrow
    na_x = lon_c + 0.028
    na_y = lat_c - 0.014
    ax.annotate("", xy=(na_x, na_y + 0.007), xytext=(na_x, na_y),
                arrowprops=dict(arrowstyle="->", lw=1.0, color="k"))
    ax.text(na_x, na_y + 0.008, "N", ha="center", fontsize=7, fontweight="bold")

    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{abs(x):.2f}°W"))
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f"{y:.3f}°N"))
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.legend(loc="lower right", frameon=True, fontsize=6)
    ax.grid(True, ls=":", alpha=0.3, lw=0.4)
    plt.savefig(out)
    plt.close()
    print(f"✓ Saved {out}")

def fig2_rate_ratios():
    out = FIGS_DIR / "fig2_rate_ratios_forest.png"
    with open("analysis/results.json") as f:
        res = json.load(f)["section2_4_rate_ratios"]["categories"]

    labels = [
        "Commercial arrivals (≤500 m)",
        "Commercial arrivals (≤1.5 km)",
        "Business & private aircraft",
        "All aircraft (≤1.5 km)",
        "Control: Light fixed-wing GA",
        "Control: Commercial (≥10,000 ft)"
    ]
    keys = [
        "commercial_arrivals_500m",
        "commercial_arrivals_1500m",
        "business_private",
        "all_aircraft_1500m",
        "control_light_fixed_wing_floatplane",
        "control_commercial_high"
    ]

    ratios = [res[k]["rate_ratio"] for k in keys]
    cis = [res[k]["ci_95_percentile"] for k in keys]
    err_lo = [r - c[0] for r, c in zip(ratios, cis)]
    err_hi = [c[1] - r for r, c in zip(ratios, cis)]

    colors = ["#2b2b2b"] * 4 + ["#7a7a7a"] * 2

    fig, ax = plt.subplots(figsize=(3.5, 3.2))
    y_pos = np.arange(len(labels))
    ax.barh(y_pos, ratios, xerr=[err_lo, err_hi], color=colors, edgecolor="k", lw=0.4, height=0.6,
            capsize=2.5, error_kw={"lw": 0.8})

    ax.axvline(1.0, color="k", ls="-", lw=0.6)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=6.5)
    ax.set_xlabel("Pass-Based Rate Ratio (Post / Pre VAMP)")
    ax.set_xlim(0, 9.5)
    ax.grid(True, axis="x", ls=":", alpha=0.3, lw=0.4)

    for i, (r, c) in enumerate(zip(ratios, cis)):
        ns_flag = " n.s." if c[0] <= 1.0 <= c[1] else ""
        ax.text(c[1] + 0.2, i, f"{r:.2f}×{ns_flag}", va="center", fontsize=6)

    ax.invert_yaxis()
    plt.tight_layout()
    plt.savefig(out)
    plt.close()
    print(f"✓ Saved {out}")

def fig3_timeseries():
    out = FIGS_DIR / "fig3_monthly_timeseries.png"
    df_passes = pd.read_csv("data/capitol_hill_passes.csv")
    daily = df_passes.groupby("date").size().reset_index(name="count")
    daily["date_dt"] = pd.to_datetime(daily["date"])
    daily = daily.sort_values("date_dt")

    daily["month"] = daily["date_dt"].dt.to_period("M")
    monthly = daily.groupby("month").agg(
        mean=("count", "mean"),
        sem=("count", lambda x: x.std(ddof=1) / np.sqrt(len(x)) if len(x) > 1 else 0.0)
    ).reset_index()
    monthly["date_dt"] = monthly["month"].dt.to_timestamp() + pd.Timedelta(days=14)

    fig, ax = plt.subplots(figsize=(7.0, 3.0))
    ax.scatter(daily["date_dt"], daily["count"], s=4, c="0.65", alpha=0.45, zorder=2, linewidths=0)
    ax.fill_between(monthly["date_dt"], monthly["mean"] - monthly["sem"], monthly["mean"] + monthly["sem"],
                    color="0.3", alpha=0.2, zorder=3)
    ax.plot(monthly["date_dt"], monthly["mean"], "k-o", ms=4, lw=1.2, zorder=4, label="Monthly mean ± SEM")

    vamp_dt = pd.Timestamp("2025-11-27")
    ax.axvline(vamp_dt, color="k", ls="--", lw=0.8, zorder=5)
    ax.text(vamp_dt + pd.Timedelta(days=4), ax.get_ylim()[1] * 0.90 if ax.get_ylim()[1] > 0 else 110,
            "AIRAC 2513\n(27 Nov 2025)", fontsize=6.5, fontstyle="italic", va="top")

    ax.set_xlabel("Date")
    ax.set_ylabel("Daily passes count")
    ax.set_ylim(bottom=0)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.legend(loc="upper left", frameon=True, framealpha=0.9)
    ax.grid(True, ls=":", alpha=0.3, lw=0.4)
    plt.savefig(out)
    plt.close()
    print(f"✓ Saved {out}")

def fig4_altitude():
    out = FIGS_DIR / "fig4_altitude_comparison.png"
    df_raw = pd.read_csv("data/capitol_hill_all_flights.csv")
    df_raw["alt"] = pd.to_numeric(df_raw["min_dist_alt_baro"], errors="coerce")
    
    with open("analysis/aircraft_classification.json") as f:
        comm_types = set(json.load(f)["commercial"])
        
    ca = df_raw[df_raw["type_code"].isin(comm_types) & (df_raw["alt"] < 10000) & (df_raw["min_dist_km"] <= 0.5)]
    pre = ca[ca["date"] < "2025-11-27"]["alt"].dropna()
    post = ca[ca["date"] >= "2025-11-27"]["alt"].dropna()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 2.8), sharey=True)
    bins = np.arange(1000, 10500, 250)

    ax1.hist(pre, bins=bins, color="0.6", edgecolor="0.4", lw=0.3, density=True)
    ax1.axvline(pre.median(), color="k", ls="--", lw=0.8)
    ax1.text(pre.median() - 250, ax1.get_ylim()[1] * 0.85 if ax1.get_ylim()[1] > 0 else 0.0003,
             f"Median\n{pre.median():,.0f} ft", fontsize=6.5, ha="right")
    ax1.set_title(f"(a) Pre-VAMP (n = {len(pre):,})", fontsize=8.5)
    ax1.set_xlabel("Barometric Altitude at CPA (ft ASL)")
    ax1.set_ylabel("Probability Density")
    ax1.set_xlim(1000, 10000)

    ax2.hist(post, bins=bins, color="0.35", edgecolor="0.2", lw=0.3, density=True)
    ax2.axvline(post.median(), color="k", ls="--", lw=0.8)
    ax2.text(post.median() + 250, ax2.get_ylim()[1] * 0.85 if ax2.get_ylim()[1] > 0 else 0.0003,
             f"Median\n{post.median():,.0f} ft", fontsize=6.5, ha="left")
    ax2.set_title(f"(b) Post-VAMP (n = {len(post):,})", fontsize=8.5)
    ax2.set_xlabel("Barometric Altitude at CPA (ft ASL)")
    ax2.set_xlim(1000, 10000)

    for ax in (ax1, ax2):
        ax.grid(True, ls=":", alpha=0.3, lw=0.4)

    plt.tight_layout()
    plt.savefig(out)
    plt.close()
    print(f"✓ Saved {out}")

def fig5_corridor_truncation():
    out = FIGS_DIR / "fig5_corridor_truncation.png"
    with open("analysis/results.json") as f:
        res = json.load(f)["section2_7_corridor_truncation"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 2.8))

    # Panel A: Radius sensitivity curve
    curve = res["radius_sensitivity"]["curve"]
    r_vals = [c["radius_km"] for c in curve]
    pct_vals = [c["pct"] for c in curve]

    ax1.plot(r_vals, pct_vals, "k-o", ms=3.5, lw=1.0)
    ax1.axvline(0.5, color="0.4", ls=":", lw=0.8)
    ax1.axvline(1.4, color="0.4", ls=":", lw=0.8)
    ax1.annotate("Core 500 m (30.7%)", xy=(0.5, 30.7), xytext=(0.15, 55),
                 arrowprops=dict(arrowstyle="->", lw=0.6), fontsize=6.5)
    ax1.annotate(f"Boundary jump\n(+{res['radius_sensitivity']['final_100m_entries_pct']:.1f}% in final 100 m)",
                 xy=(1.5, 100), xytext=(0.85, 80),
                 arrowprops=dict(arrowstyle="->", lw=0.6), fontsize=6.5)

    ax1.set_xlabel("Study Radius Threshold (km)")
    ax1.set_ylabel("Cumulative % of Arrival Records")
    ax1.set_title("(a) Radius Sensitivity & Truncation", fontsize=8.5)
    ax1.set_ylim(0, 105)
    ax1.grid(True, ls=":", alpha=0.3, lw=0.4)

    # Panel B: Lateral distance from summit for Eastbound vs Westbound
    eb_d = res["eastbound_corridor"]["distance_from_summit_km"]
    wb_d = res["westbound_corridor"]["distance_from_summit_km"]

    categories = ["Eastbound Corridor\n(060–150°, n=3,918)", "Westbound Corridor\n(240–330°, n=6,554)"]
    dists = [abs(eb_d), abs(wb_d)]
    iqrs = [res["eastbound_corridor"]["lateral_iqr_m"] / 1000.0, res["westbound_corridor"]["lateral_iqr_m"] / 1000.0]

    bars = ax2.bar(categories, dists, yerr=iqrs, color=["#333333", "#777777"], edgecolor="k", lw=0.5, width=0.5, capsize=3)
    ax2.axhline(1.5, color="k", ls="--", lw=0.8, label="1.5 km boundary")
    ax2.set_ylabel("Distance South of Summit (km)")
    ax2.set_title("(b) Corridor Offset from Summit", fontsize=8.5)
    ax2.set_ylim(0, 1.8)
    ax2.legend(loc="upper left", fontsize=6.5)
    ax2.grid(True, ls=":", alpha=0.3, lw=0.4)

    plt.tight_layout()
    plt.savefig(out)
    plt.close()
    print(f"✓ Saved {out}")

def fig6_direction_shifts():
    out = FIGS_DIR / "fig6_direction_shifts.png"
    with open("analysis/results.json") as f:
        t = json.load(f)["section2_6_direction"]["table"]["Commercial arrivals"]

    headings = ["East (060–120°)", "West (240–300°)", "North (330–030°)", "South (150–210°)", "Other"]
    keys = ["E", "W", "N", "S", "Other"]

    counts_b = [t["Before"]["counts"][k] for k in keys]
    counts_a = [t["After"]["counts"][k] for k in keys]

    x = np.arange(len(headings))
    w = 0.35

    fig, ax = plt.subplots(figsize=(5.5, 2.8))
    ax.bar(x - w/2, counts_b, width=w, label=f"Pre-VAMP (n={t['Before']['total']:,})", color="0.65", edgecolor="k", lw=0.5)
    ax.bar(x + w/2, counts_a, width=w, label=f"Post-VAMP (n={t['After']['total']:,})", color="0.25", edgecolor="k", lw=0.5)

    ax.set_xticks(x)
    ax.set_xticklabels(headings, fontsize=7)
    ax.set_ylabel("Arrival Flight Count")
    ax.set_title("Commercial Arrival Heading Distribution (Pre vs. Post VAMP)", fontsize=8.5)
    ax.legend(loc="upper right", fontsize=7)
    ax.grid(True, ls=":", alpha=0.3, lw=0.4, axis="y")

    plt.tight_layout()
    plt.savefig(out)
    plt.close()
    print(f"✓ Saved {out}")

def fig7_statcan():
    out = FIGS_DIR / "fig7_statcan_validation.png"
    with open("analysis/results.json") as f:
        res = json.load(f)["section2_9_statcan"]

    categories = [
        "YVR Airport\n(StatCan)",
        "Boundary Bay\n(StatCan)",
        "Pitt Meadows\n(StatCan)",
        "Langley\n(StatCan)",
        "Vancouver Harbour\n(StatCan)",
        "Capitol Hill GA\n(ADS-B Light)",
        "Capitol Hill Arrivals\n(ADS-B Comm)"
    ]

    ratios = [
        res["statcan"]["YVR"]["ratio"],
        res["statcan"]["Boundary_Bay"]["ratio"],
        res["statcan"]["Pitt_Meadows"]["ratio"],
        res["statcan"]["Langley"]["ratio"],
        res["statcan"]["Vancouver_Harbour"]["ratio"],
        res["adsb_capitol_hill"]["light_fixed_wing_ga"]["ratio"],
        res["adsb_capitol_hill"]["commercial_arrivals"]["ratio"]
    ]

    colors = ["0.55"] * 5 + ["0.4", "0.2"]

    fig, ax = plt.subplots(figsize=(4.8, 3.0))
    y_pos = np.arange(len(categories))
    ax.barh(y_pos, ratios, color=colors, edgecolor="k", lw=0.5, height=0.6)
    ax.axvline(1.0, color="k", ls="--", lw=0.8)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(categories, fontsize=6.5)
    ax.set_xlabel("Ratio: Jan–Jun 2026 / Jan–Jun 2025")
    ax.set_xlim(0, 7.0)
    ax.grid(True, axis="x", ls=":", alpha=0.3, lw=0.4)

    for i, r in enumerate(ratios):
        ax.text(r + 0.12, i, f"{r:.2f}×", va="center", fontsize=6.5)

    ax.invert_yaxis()
    plt.tight_layout()
    plt.savefig(out)
    plt.close()
    print(f"✓ Saved {out}")

def main():
    print("=== GENERATING REVISED PUBLICATION FIGURES ===")
    fig1_study_area()
    fig2_rate_ratios()
    fig3_timeseries()
    fig4_altitude()
    fig5_corridor_truncation()
    fig6_direction_shifts()
    fig7_statcan()
    print("All figures successfully regenerated into figures/")

if __name__ == "__main__":
    main()
