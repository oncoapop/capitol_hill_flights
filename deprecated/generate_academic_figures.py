"""
Generate compact, journal-style figures for the academic manuscript.
All figures use serif fonts, muted colours, and are sized for single- or
double-column journal layouts (3.5 in or 7.0 in width, 300 DPI).
"""
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.patches as mpatches
import matplotlib.dates as mdates

from config import (
    DATABASE_PATH,
    WORKSPACE_DIR,
    CENTER_LAT,
    CENTER_LON,
    RADIUS_KM,
    BBOX_LAT_MIN,
    BBOX_LAT_MAX,
    BBOX_LON_MIN,
    BBOX_LON_MAX,
    LOCAL_TIMEZONE,
)

FIGURES_DIR = WORKSPACE_DIR / "academic_figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# ── Journal-quality RC parameters ────────────────────────────────────────
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

VAMP_DATE = "2025-11-27"
MAX_DATE = "2026-08-31"


def _load_flights() -> pd.DataFrame:
    conn = sqlite3.connect(DATABASE_PATH)
    df = pd.read_sql_query("SELECT * FROM flights WHERE date <= '2026-08-31' ORDER BY cpa_utc", conn)
    conn.close()
    df["cpa_dt"] = pd.to_datetime(df["cpa_utc"], format="ISO8601", utc=True).dt.tz_convert(LOCAL_TIMEZONE)
    df["date_dt"] = pd.to_datetime(df["date"])
    df["month"] = df["cpa_dt"].dt.to_period("M")
    df["alt_ft"] = pd.to_numeric(df["min_dist_alt_baro"], errors="coerce")
    return df


# ── Figure 1: Study Area Map ────────────────────────────────────────────
def fig1_study_area(output: Path = FIGURES_DIR / "fig1_study_area.png"):
    fig, ax = plt.subplots(figsize=(3.5, 2.8))
    lat_c, lon_c = CENTER_LAT, CENTER_LON
    d_lat = RADIUS_KM / 111.19
    d_lon = RADIUS_KM / 72.54
    pad_lon, pad_lat = 0.035, 0.020

    ax.set_xlim(lon_c - pad_lon, lon_c + pad_lon)
    ax.set_ylim(lat_c - pad_lat, lat_c + pad_lat)

    # Water (Burrard Inlet)
    x_w = np.linspace(lon_c - pad_lon, lon_c + pad_lon, 80)
    y_w = 49.293 + 0.002 * np.sin((x_w - lon_c) * 60)
    ax.fill_between(x_w, y_w, lat_c + pad_lat, color="#d0dde8", alpha=0.7)
    ax.fill_between(x_w, lat_c - pad_lat, y_w, color="#f5f5f5", alpha=0.9)

    # Bounding box
    bb = mpatches.Rectangle(
        (BBOX_LON_MIN, BBOX_LAT_MIN),
        BBOX_LON_MAX - BBOX_LON_MIN,
        BBOX_LAT_MAX - BBOX_LAT_MIN,
        lw=0.8, edgecolor="0.4", facecolor="none", ls="--",
    )
    ax.add_patch(bb)

    # 1.5 km circle
    circ = mpatches.Ellipse(
        (lon_c, lat_c), width=d_lon * 2, height=d_lat * 2,
        edgecolor="k", facecolor="#dddddd", alpha=0.35, lw=1.2,
    )
    ax.add_patch(circ)

    # Centre point
    ax.plot(lon_c, lat_c, "k*", ms=8, zorder=10)
    ax.annotate("Capitol Hill\n(115 m ASL)", (lon_c, lat_c),
                xytext=(8, 6), textcoords="offset points", fontsize=6.5, fontstyle="italic")

    # Scale bar (1 km)
    sb_x = lon_c - 0.031
    sb_y = lat_c - 0.017
    sb_len = 1.0 / 72.54
    ax.plot([sb_x, sb_x + sb_len], [sb_y, sb_y], "k-", lw=2)
    ax.text(sb_x + sb_len / 2, sb_y + 0.001, "1 km", ha="center", fontsize=6)

    # North arrow
    na_x = lon_c + 0.030
    na_y = lat_c - 0.012
    ax.annotate("", xy=(na_x, na_y + 0.006), xytext=(na_x, na_y),
                arrowprops=dict(arrowstyle="->", lw=1.0, color="k"))
    ax.text(na_x, na_y + 0.007, "N", ha="center", fontsize=7, fontweight="bold")

    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{abs(x):.2f}°W"))
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f"{y:.3f}°N"))
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.grid(True, ls=":", alpha=0.3, lw=0.4)

    plt.savefig(output)
    plt.close()
    print(f"  ✓ {output.name}")


# ── Figure 2: Monthly Time Series ────────────────────────────────────────
def fig2_monthly_timeseries(df: pd.DataFrame, output: Path = FIGURES_DIR / "fig2_monthly_timeseries.png"):
    daily = df.groupby("date").size().reset_index(name="n")
    daily["date_dt"] = pd.to_datetime(daily["date"])
    daily = daily.sort_values("date_dt")

    # Monthly stats
    daily["month"] = daily["date_dt"].dt.to_period("M")
    monthly = daily.groupby("month").agg(
        mean=("n", "mean"),
        sem=("n", lambda x: x.std(ddof=1) / np.sqrt(len(x)) if len(x) > 1 else 0),
        median=("n", "median"),
    ).reset_index()
    monthly["date_dt"] = monthly["month"].dt.to_timestamp() + pd.Timedelta(days=14)

    fig, ax = plt.subplots(figsize=(7.0, 3.0))

    # Scatter daily counts (small grey dots)
    ax.scatter(daily["date_dt"], daily["n"], s=4, c="0.65", alpha=0.45, zorder=2, linewidths=0)

    # Monthly mean ± SEM ribbon
    ax.fill_between(
        monthly["date_dt"],
        monthly["mean"] - monthly["sem"],
        monthly["mean"] + monthly["sem"],
        color="0.3", alpha=0.2, zorder=3,
    )
    ax.plot(monthly["date_dt"], monthly["mean"], "k-o", ms=4, lw=1.2, zorder=4, label="Monthly mean ± SEM")

    # VAMP vertical line
    vamp_dt = pd.Timestamp(VAMP_DATE)
    ax.axvline(vamp_dt, color="k", ls="--", lw=0.8, zorder=5)
    ax.text(vamp_dt + pd.Timedelta(days=5), ax.get_ylim()[1] * 0.92 if ax.get_ylim()[1] > 0 else 100,
            "AIRAC 2513\n(27 Nov 2025)", fontsize=6.5, fontstyle="italic", va="top")

    ax.set_xlabel("Date")
    ax.set_ylabel("Daily overflight count")
    ax.set_ylim(bottom=0)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.legend(loc="upper left", frameon=True, framealpha=0.9)
    ax.grid(True, ls=":", alpha=0.3, lw=0.4)

    plt.savefig(output)
    plt.close()
    print(f"  ✓ {output.name}")


# ── Figure 3: Altitude Comparison (Pre vs Post) ─────────────────────────
def fig3_altitude_comparison(df: pd.DataFrame, output: Path = FIGURES_DIR / "fig3_altitude_comparison.png"):
    df_alt = df.dropna(subset=["alt_ft"])
    df_alt = df_alt[(df_alt["alt_ft"] > 0) & (df_alt["alt_ft"] <= 40000)]

    pre = df_alt[df_alt["date"] < VAMP_DATE]["alt_ft"]
    post = df_alt[df_alt["date"] >= VAMP_DATE]["alt_ft"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 3.0), sharey=True)

    bins = np.arange(0, 42000, 500)
    ax1.hist(pre, bins=bins, color="0.6", edgecolor="0.4", lw=0.3, density=True)
    ax1.axvline(pre.median(), color="k", ls="--", lw=0.8)
    ax1.text(pre.median() + 300, ax1.get_ylim()[1] * 0.85 if ax1.get_ylim()[1] > 0 else 0.0003,
             f"Median\n{pre.median():,.0f} ft", fontsize=6.5)
    ax1.set_title(f"Pre-VAMP (n = {len(pre):,})", fontsize=9)
    ax1.set_xlabel("Barometric altitude (ft)")
    ax1.set_ylabel("Density")
    ax1.set_xlim(0, 20000)

    ax2.hist(post, bins=bins, color="0.35", edgecolor="0.2", lw=0.3, density=True)
    ax2.axvline(post.median(), color="k", ls="--", lw=0.8)
    ax2.text(post.median() + 300, ax2.get_ylim()[1] * 0.85 if ax2.get_ylim()[1] > 0 else 0.0003,
             f"Median\n{post.median():,.0f} ft", fontsize=6.5)
    ax2.set_title(f"Post-VAMP (n = {len(post):,})", fontsize=9)
    ax2.set_xlabel("Barometric altitude (ft)")
    ax2.set_xlim(0, 20000)

    for ax in (ax1, ax2):
        ax.grid(True, ls=":", alpha=0.3, lw=0.4)

    fig.suptitle("")  # no suptitle – caption goes below in manuscript
    plt.tight_layout()
    plt.savefig(output)
    plt.close()
    print(f"  ✓ {output.name}")


# ── Figure 4: Diurnal Heatmap (compact) ──────────────────────────────────
def fig4_diurnal_heatmap(df: pd.DataFrame, output: Path = FIGURES_DIR / "fig4_diurnal_heatmap.png"):
    df_h = df.copy()
    df_h["hour"] = df_h["cpa_dt"].dt.hour
    df_h["month_str"] = df_h["cpa_dt"].dt.strftime("%Y-%m")

    pivot = df_h.groupby(["hour", "month_str"]).size().unstack(fill_value=0)
    pivot = pivot.reindex(range(24), fill_value=0)

    fig, ax = plt.subplots(figsize=(7.0, 3.2))
    import matplotlib.colors as mcolors
    im = ax.imshow(pivot.values, aspect="auto", cmap="Greys", interpolation="nearest",
                   origin="upper")
    ax.set_yticks(range(24))
    ax.set_yticklabels([f"{h:02d}:00" for h in range(24)], fontsize=6)
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=45, ha="right", fontsize=6)
    ax.set_xlabel("Month")
    ax.set_ylabel("Hour of day (Pacific)")
    cbar = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
    cbar.set_label("Flight count", fontsize=7)
    cbar.ax.tick_params(labelsize=6)

    plt.tight_layout()
    plt.savefig(output)
    plt.close()
    print(f"  ✓ {output.name}")


# ── Figure 5: Negative Control Bar Chart ─────────────────────────────────
def fig5_negative_controls(output: Path = FIGURES_DIR / "fig5_negative_controls.png"):
    """Rate ratios (post/pre) with 95% bootstrap CI for intervention vs. control categories."""
    categories = [
        "Arriving commercial\n(≤500 m)",
        "All arriving commercial\n(≤1.5 km)",
        "Business & private jets\n(≤1.5 km)",
        "All aircraft\n(≤1.5 km)",
        "Control: Light aircraft,\nfloatplanes, helicopters",
        "Control: Commercial\n≥10,000 ft",
    ]
    ratios = [6.04, 7.03, 2.47, 3.25, 0.97, 0.90]
    ci_lo = [5.24, 6.40, 2.17, 3.03, 0.85, 0.69]
    ci_hi = [7.03, 7.76, 2.83, 3.49, 1.10, 1.17]

    err_lo = [r - lo for r, lo in zip(ratios, ci_lo)]
    err_hi = [hi - r for r, hi in zip(ratios, ci_hi)]

    colors = ["0.25"] * 4 + ["0.65"] * 2

    fig, ax = plt.subplots(figsize=(3.5, 3.5))
    y_pos = np.arange(len(categories))
    bars = ax.barh(y_pos, ratios, xerr=[err_lo, err_hi],
                   color=colors, edgecolor="k", lw=0.4, height=0.6,
                   capsize=2.5, error_kw={"lw": 0.7})

    ax.axvline(1.0, color="k", ls="-", lw=0.6)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(categories, fontsize=6.5)
    ax.set_xlabel("Rate ratio (post / pre VAMP)")
    ax.set_xlim(0, 9)
    ax.grid(True, axis="x", ls=":", alpha=0.3, lw=0.4)

    # Annotate values
    for i, (r, lo, hi) in enumerate(zip(ratios, ci_lo, ci_hi)):
        label = f"{r:.2f}×" if r > 1.5 else f"{r:.2f}× n.s."
        ax.text(r + (hi - r) + 0.15, i, label, va="center", fontsize=6)

    ax.invert_yaxis()
    plt.tight_layout()
    plt.savefig(output)
    plt.close()
    print(f"  ✓ {output.name}")


# ── Main ─────────────────────────────────────────────────────────────────
def main():
    print("Generating academic journal figures …")
    df = _load_flights()
    fig1_study_area()
    fig2_monthly_timeseries(df)
    fig3_altitude_comparison(df)
    fig4_diurnal_heatmap(df)
    fig5_negative_controls()
    print(f"\nAll figures saved to {FIGURES_DIR}/")


if __name__ == "__main__":
    main()
