"""
Comprehensive Aggregations, Analysis, CSV Exports, Heatmap, and Publication-Quality Unified Box Plot.
"""
import argparse
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from config import (
    DATABASE_PATH,
    OUTPUT_DIR,
    HEATMAP_IMAGE_PATH,
    WORKSPACE_DIR,
    LOCAL_TIMEZONE,
)
from database import fetch_all_flights_df, fetch_processing_summary, get_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("analyze")

BOXPLOT_IMAGE_PATH = WORKSPACE_DIR / "monthly_overflights_boxplot.png"
HEATMAP_IMAGE_PATH = WORKSPACE_DIR / "flight_density_heatmap.png"


def generate_daily_counts(df: pd.DataFrame, max_date: str = "2026-08-31") -> pd.DataFrame:
    """Generate summary table of total flight counts per day."""
    if df.empty:
        return pd.DataFrame(columns=["date", "total_flights", "unique_aircraft", "top_aircraft_type", "min_altitude_ft", "avg_altitude_ft"])

    df_clean = df.copy()
    if max_date:
        df_clean = df_clean[df_clean["date"] <= max_date]

    df_clean["alt_num"] = pd.to_numeric(df_clean["min_dist_alt_baro"], errors="coerce")

    daily = df_clean.groupby("date").agg(
        total_flights=("icao", "count"),
        unique_aircraft=("icao", "nunique"),
        min_altitude_ft=("alt_num", "min"),
        avg_altitude_ft=("alt_num", "mean"),
    ).reset_index()

    top_types = (
        df_clean.dropna(subset=["type_code"])
        .groupby(["date", "type_code"])
        .size()
        .reset_index(name="count")
        .sort_values(["date", "count"], ascending=[True, False])
        .drop_duplicates("date")
        .set_index("date")["type_code"]
    )
    daily["top_aircraft_type"] = daily["date"].map(top_types).fillna("N/A")
    daily["avg_altitude_ft"] = daily["avg_altitude_ft"].round(1)

    return daily.sort_values("date")


def generate_monthly_summary(df: pd.DataFrame, max_month: str = "2026-08") -> pd.DataFrame:
    """Generate monthly summary of overflights, daily high/low/median/mean, and SEM."""
    if df.empty:
        return pd.DataFrame(columns=["month", "total_flights", "days_analyzed", "daily_min", "daily_max", "daily_median", "daily_mean", "sem", "unique_aircraft"])

    df_clean = df.copy()
    dt_series = pd.to_datetime(df_clean["cpa_utc"], utc=True, errors="coerce").dt.tz_convert(LOCAL_TIMEZONE)
    df_clean["month"] = dt_series.dt.strftime("%Y-%m")
    df_clean["day"] = dt_series.dt.strftime("%Y-%m-%d")

    if max_month:
        df_clean = df_clean[df_clean["month"] <= max_month]

    daily_counts = df_clean.groupby(["month", "day"]).size().reset_index(name="flight_count")

    rows = []
    for month, group in daily_counts.groupby("month"):
        counts = group["flight_count"].values
        n = len(counts)
        mean_val = float(np.mean(counts))
        median_val = float(np.median(counts))
        min_val = int(np.min(counts))
        max_val = int(np.max(counts))
        
        sem_val = float(np.std(counts, ddof=1) / np.sqrt(n)) if n > 1 else 0.0

        month_flights = df_clean[df_clean["month"] == month]
        total_fl = len(month_flights)
        unique_ac = month_flights["icao"].nunique()

        rows.append({
            "month": month,
            "total_flights": total_fl,
            "days_analyzed": n,
            "daily_min": min_val,
            "daily_max": max_val,
            "daily_median": round(median_val, 1),
            "daily_mean": round(mean_val, 1),
            "sem": round(sem_val, 2),
            "unique_aircraft": unique_ac,
        })

    monthly_df = pd.DataFrame(rows).sort_values("month")
    return monthly_df


def plot_complete_months_boxplot_with_dots(
    df: pd.DataFrame,
    output_path: Path = BOXPLOT_IMAGE_PATH,
    max_month: str = "2026-08",
) -> None:
    """
    Generate a clean, unified chart showing monthly overflights for complete months (Jan 2025 - Aug 2026).
    Includes:
      - Embedded top summary table showing High, Median, Low, Mean, Total flights, and Days in archive
      - Box plots with IQR and Min-to-Max whiskers
      - Prominent median lines
      - Monthly mean points with SEM
      - Numbered day badges for all observed daily flight count points
    """
    if df.empty:
        logger.warning("No flight data available to plot box plot.")
        return

    df_clean = df.copy()
    dt_series = pd.to_datetime(df_clean["cpa_utc"], utc=True, errors="coerce").dt.tz_convert(LOCAL_TIMEZONE)
    df_clean["month"] = dt_series.dt.strftime("%Y-%m")
    df_clean["day"] = dt_series.dt.strftime("%Y-%m-%d")
    df_clean["day_num"] = dt_series.dt.day

    if max_month:
        df_complete = df_clean[df_clean["month"] <= max_month].copy()
    else:
        df_complete = df_clean.copy()

    if df_complete.empty:
        logger.warning(f"No data found up to {max_month}.")
        return

    # Daily aggregation with day number
    daily_counts = (
        df_complete.groupby(["month", "day", "day_num"])
        .size()
        .reset_index(name="flight_count")
    )
    monthly_stats = generate_monthly_summary(df_complete, max_month=max_month)

    months = sorted(monthly_stats["month"].unique())
    x_positions = np.arange(len(months))
    month_to_x = {m: i for i, m in enumerate(months)}

    boxplot_data = [daily_counts[daily_counts["month"] == m]["flight_count"].values for m in months]

    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    
    fig = plt.figure(figsize=(22, 12), dpi=220)
    gs = fig.add_gridspec(2, 1, height_ratios=[0.24, 1.0], hspace=0.16)
    
    ax_table = fig.add_subplot(gs[0])
    ax = fig.add_subplot(gs[1])

    # -------------------------------------------------------------
    # 1. TOP SUMMARY TABLE (High, Median, Low, Mean, Total)
    # -------------------------------------------------------------
    ax_table.axis("off")
    
    table_columns = months
    row_labels = ["High (Max)", "Median", "Low (Min)", "Mean", "Total Flights", "Days in Archive"]
    
    table_data = []
    # High row
    table_data.append([str(row["daily_max"]) for _, row in monthly_stats.iterrows()])
    # Median row
    table_data.append([f"{row['daily_median']:.1f}".rstrip('0').rstrip('.') for _, row in monthly_stats.iterrows()])
    # Low row
    table_data.append([str(row["daily_min"]) for _, row in monthly_stats.iterrows()])
    # Mean row
    table_data.append([f"{row['daily_mean']:.1f}" for _, row in monthly_stats.iterrows()])
    # Total row
    table_data.append([f"{row['total_flights']:,}" for _, row in monthly_stats.iterrows()])
    # Days row
    table_data.append([str(row["days_analyzed"]) for _, row in monthly_stats.iterrows()])

    table = ax_table.table(
        cellText=table_data,
        rowLabels=row_labels,
        colLabels=table_columns,
        cellLoc="center",
        loc="center",
        bbox=[0.0, 0.0, 1.0, 0.95],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8.5)

    for (row_idx, col_idx), cell in table.get_celld().items():
        cell.set_edgecolor("#cccccc")
        cell.set_linewidth(0.8)
        if row_idx == 0:
            cell.set_facecolor("#1c3d5a")
            cell.set_text_props(color="white", weight="bold", fontsize=9)
        elif col_idx == -1:
            cell.set_facecolor("#f0f4f8")
            cell.set_text_props(weight="bold", color="#1c3d5a", fontsize=8.5)
            if "High" in row_labels[row_idx - 1]:
                cell.set_text_props(color="#a81a04", weight="bold")
            elif "Low" in row_labels[row_idx - 1]:
                cell.set_text_props(color="#004488", weight="bold")
            elif "Median" in row_labels[row_idx - 1]:
                cell.set_text_props(color="#d9381e", weight="bold")
        else:
            if row_idx == 1:
                cell.set_facecolor("#fff0ed")
                cell.set_text_props(color="#a81a04", weight="bold")
            elif row_idx == 2:
                cell.set_facecolor("#fef5ea")
                cell.set_text_props(color="#d9381e", weight="bold")
            elif row_idx == 3:
                cell.set_facecolor("#edf4fb")
                cell.set_text_props(color="#004488", weight="bold")
            elif row_idx == 4:
                cell.set_facecolor("#f2f9f2")
                cell.set_text_props(color="#2b8a3e")
            elif row_idx == 5:
                cell.set_facecolor("#f8f9fa")
                cell.set_text_props(weight="bold", color="#1c3d5a")
            else:
                cell.set_facecolor("#ffffff")

    ax_table.set_title(
        f"Monthly Overflight Summary Statistics (Full Archive Census: {months[0]} – {months[-1]})",
        fontsize=12.5,
        fontweight="bold",
        pad=10,
        color="#1c3d5a",
    )

    # -------------------------------------------------------------
    # 2. MAIN BOX PLOT WITH NUMBERED DAY DOTS
    # -------------------------------------------------------------
    bp = ax.boxplot(
        boxplot_data,
        positions=x_positions,
        widths=0.60,
        whis=(0, 100),
        patch_artist=True,
        showmeans=False,
        showfliers=False,
        boxprops=dict(facecolor="#d0e1f9", color="#1c3d5a", alpha=0.45, linewidth=1.5),
        whiskerprops=dict(color="#1c3d5a", linewidth=1.5, linestyle="-"),
        capprops=dict(color="#1c3d5a", linewidth=2.0),
        medianprops=dict(color="#d9381e", linewidth=3.0),
    )

    # Mean marker with SEM error bars
    means = monthly_stats["daily_mean"].values
    sems = monthly_stats["sem"].values
    
    ax.errorbar(
        x_positions,
        means,
        yerr=sems,
        fmt="none",
        ecolor="#2b8a3e",
        elinewidth=2.0,
        capsize=4.5,
        capthick=1.8,
        alpha=0.95,
        zorder=4,
    )
    ax.scatter(
        x_positions,
        means,
        marker="D",
        s=70,
        color="#2b8a3e",
        edgecolors="black",
        linewidths=1.2,
        zorder=5,
        label="Monthly Mean (± SEM)",
    )

    # Plot Day # Points with controlled jitter
    np.random.seed(42)
    daily_counts["x_idx"] = daily_counts["month"].map(month_to_x)
    
    jitter_list = []
    for _, row in daily_counts.iterrows():
        month_count = len(daily_counts[daily_counts["month"] == row["month"]])
        jitter_span = 0.25 if month_count > 10 else 0.10
        jitter_list.append(np.random.uniform(-jitter_span, jitter_span))
    daily_counts["plot_x"] = daily_counts["x_idx"] + jitter_list

    # Draw circular badges
    badge_size = 175
    ax.scatter(
        daily_counts["plot_x"],
        daily_counts["flight_count"],
        s=badge_size,
        c="#ff5722",
        edgecolors="#7f2704",
        linewidths=1.2,
        alpha=0.88,
        zorder=6,
        label="Daily Count (Badge shows Day of Month)",
    )

    # Render Day Number inside each circle
    for _, row in daily_counts.iterrows():
        ax.text(
            row["plot_x"],
            row["flight_count"],
            f"{int(row['day_num'])}",
            ha="center",
            va="center",
            fontsize=7.5,
            fontweight="bold",
            color="white",
            zorder=7,
        )

    # Axis Labels & Styling
    ax.set_xlabel("Month (YYYY-MM)", fontsize=12, fontweight="bold", labelpad=10)
    ax.set_ylabel("Daily Overflight Count (Flights / Day)", fontsize=12, fontweight="bold", labelpad=10)
    ax.set_xticks(x_positions)
    ax.set_xticklabels(months, rotation=45, ha="right", fontsize=10.5, fontweight="semibold")
    
    max_y = daily_counts["flight_count"].max()
    ax.set_ylim(bottom=0, top=max_y * 1.10 + 5)
    ax.grid(True, linestyle=":", alpha=0.55, which="both")

    # Legend
    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D
    legend_elements = [
        Patch(facecolor="#d0e1f9", edgecolor="#1c3d5a", alpha=0.6, label="IQR Box (25th–75th Percentile) & Min–Max Whiskers"),
        Line2D([0], [0], color="#d9381e", linewidth=3.0, linestyle="-", label="Median Line"),
        Line2D([0], [0], marker="D", color="#2b8a3e", markerfacecolor="#2b8a3e", markeredgecolor="black", markersize=8, label="Monthly Mean (± Standard Error)"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#ff5722", markeredgecolor="#7f2704", markersize=10, label="Daily Points (Number = Day of Month)"),
    ]
    ax.legend(handles=legend_elements, loc="upper left", frameon=True, fontsize=10.5, shadow=True, fancybox=True)

    fig.suptitle(
        f"Capitol Hill (Burnaby, BC) Aircraft Overflight Distribution by Month ({months[0]} – {months[-1]})\n"
        f"Full Archive Census ({len(months)} Complete Months) | Radius: 1.5 km | Center: 49.2869° N, 122.9853° W",
        fontsize=14.5,
        fontweight="bold",
        y=0.985,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close()
    logger.info(f"Saved complete months box plot with day badges and top table to {output_path}")


def generate_heatmap(df: pd.DataFrame, output_path: Path = HEATMAP_IMAGE_PATH, max_month: str = "2026-08") -> None:
    """Generate 24-hour monthly density heatmap and supporting distributions."""
    if df.empty:
        logger.warning("No flight data available to plot heatmap.")
        return

    df_clean = df.copy()
    dt_series = pd.to_datetime(df_clean["cpa_utc"], utc=True, errors="coerce").dt.tz_convert(LOCAL_TIMEZONE)
    df_clean["month"] = dt_series.dt.strftime("%Y-%m")
    df_clean["hour"] = dt_series.dt.hour

    if max_month:
        df_clean = df_clean[df_clean["month"] <= max_month]

    hourly_monthly = df_clean.groupby(["hour", "month"]).size().unstack(fill_value=0)
    all_hours = pd.Index(range(24), name="hour")
    hourly_monthly = hourly_monthly.reindex(all_hours, fill_value=0)

    fig = plt.figure(figsize=(19, 12), dpi=200)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.4, 1.0], hspace=0.3, wspace=0.25)
    ax_heatmap = fig.add_subplot(gs[0, :])
    ax_altitude = fig.add_subplot(gs[1, 0])
    ax_types = fig.add_subplot(gs[1, 1])

    # Heatmap
    sns.heatmap(
        hourly_monthly,
        cmap="YlOrRd",
        annot=False,
        linewidths=0.5,
        linecolor="#f0f0f0",
        cbar_kws={"label": "Flight Count"},
        ax=ax_heatmap,
    )
    ax_heatmap.set_title(
        f"Capitol Hill (Burnaby, BC) Aircraft Overflight Density Heatmap (Radius: 1.5 km)\n"
        f"Complete Census across {len(hourly_monthly.columns)} Months ({len(df_clean):,} Total Overflights)",
        fontsize=13,
        fontweight="bold",
        pad=12,
    )
    ax_heatmap.set_xlabel("Month", fontsize=11, fontweight="bold")
    ax_heatmap.set_ylabel(f"Hour of Day (Local Pacific Time ({LOCAL_TIMEZONE}))", fontsize=11, fontweight="bold")
    ax_heatmap.set_yticklabels([f"{h:02d}:00" for h in range(24)], rotation=0)
    ax_heatmap.tick_params(axis="x", rotation=45)

    # Altitude histogram
    altitudes = pd.to_numeric(df_clean["min_dist_alt_baro"], errors="coerce").dropna()
    altitudes = altitudes[altitudes <= 40000]
    sns.histplot(altitudes, bins=35, kde=True, ax=ax_altitude, color="#1c3d5a")
    median_alt = altitudes.median() if not altitudes.empty else 0
    ax_altitude.axvline(median_alt, color="red", linestyle="--", linewidth=1.8, label=f"Median: {median_alt:,.0f} ft")
    ax_altitude.set_title("Altitude Distribution at Closest Approach", fontsize=12, fontweight="bold")
    ax_altitude.set_xlabel("Barometric Altitude (ft)", fontsize=10, fontweight="bold")
    ax_altitude.set_ylabel("Number of Flights", fontsize=10, fontweight="bold")
    ax_altitude.legend(fontsize=10)

    # Top Aircraft Types
    top_types = df_clean["type_code"].dropna().value_counts().head(10)
    sns.barplot(x=top_types.values, y=top_types.index, ax=ax_types, hue=top_types.index, palette="Blues_r", legend=False)
    ax_types.set_title("Top 10 Aircraft Types Over Capitol Hill", fontsize=12, fontweight="bold")
    ax_types.set_xlabel("Number of Flights", fontsize=10, fontweight="bold")
    ax_types.set_ylabel("Aircraft Type Code", fontsize=10, fontweight="bold")
    for i, v in enumerate(top_types.values):
        ax_types.text(v + (max(top_types.values) * 0.01), i, f"{v:,}", va="center", fontsize=9, fontweight="bold")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close()
    logger.info(f"Saved complete heatmap to {output_path}")


def export_aggregations(output_dir: Path = OUTPUT_DIR, db_path: Path = DATABASE_PATH, max_month: str = "2026-08") -> None:
    """Compute and export all aggregated tables, CSVs, heatmap, and box plot."""
    output_dir.mkdir(parents=True, exist_ok=True)
    df = fetch_all_flights_df(db_path)

    if df.empty:
        logger.warning("Database contains no flights. Skipping CSV export.")
        return

    logger.info(f"Loaded {len(df)} flight records from database.")

    # 1. Export All Flights
    all_flights_csv = output_dir / "capitol_hill_all_flights.csv"
    df.to_csv(all_flights_csv, index=False)
    logger.info(f"Exported all flights to {all_flights_csv}")

    # 2. Export Daily Flight Counts (Complete Months)
    daily_df = generate_daily_counts(df, max_date=f"{max_month}-31")
    daily_csv = output_dir / "daily_flight_counts_complete_months.csv"
    daily_df.to_csv(daily_csv, index=False)
    logger.info(f"Exported daily flight counts (complete months) to {daily_csv}")

    # 3. Export Monthly Summary with High/Low/Median/SEM
    monthly_df = generate_monthly_summary(df, max_month=max_month)
    monthly_csv = output_dir / "monthly_flight_summary_complete_months.csv"
    monthly_df.to_csv(monthly_csv, index=False)
    logger.info(f"Exported monthly flight summary (complete months) to {monthly_csv}")

    # 4. Generate Visualizations
    plot_complete_months_boxplot_with_dots(df, output_path=BOXPLOT_IMAGE_PATH, max_month=max_month)
    generate_heatmap(df, output_path=HEATMAP_IMAGE_PATH, max_month=max_month)

    print("\n" + "=" * 90)
    print(f"CAPITOL HILL (BURNABY, BC) COMPLETE MONTHS OVERFLIGHT SUMMARY ({monthly_df['month'].iloc[0]} – {monthly_df['month'].iloc[-1]})")
    print("=" * 90)
    print(f"Total Flights Tracked: {monthly_df['total_flights'].sum():,}")
    print(f"Unique Aircraft: {df[df['date'] <= f'{max_month}-31']['icao'].nunique():,}")
    print(f"Complete Months Count: {monthly_df['month'].nunique()} months")
    print(f"Total Days Analyzed: {monthly_df['days_analyzed'].sum()} days")
    print("\n--- Monthly Stats: High, Low, Median, Mean & SEM ---")
    print(monthly_df.to_string(index=False))
    print("=" * 90 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Analyze Capitol Hill Flight Data")
    parser.add_argument("--export-dir", type=str, default=str(OUTPUT_DIR), help="Output directory for CSV exports")
    parser.add_argument("--boxplot-out", type=str, default=str(BOXPLOT_IMAGE_PATH), help="Output path for box plot PNG")
    parser.add_argument("--heatmap-out", type=str, default=str(HEATMAP_IMAGE_PATH), help="Output path for heatmap PNG")
    parser.add_argument("--max-month", type=str, default="2026-08", help="Latest month to include (e.g. 2026-08)")

    args = parser.parse_args()

    df = fetch_all_flights_df(DATABASE_PATH)
    if df.empty:
        print("No flight records found in database. Run pipeline.py first to extract flights.")
        return

    export_aggregations(output_dir=Path(args.export_dir), db_path=DATABASE_PATH, max_month=args.max_month)


if __name__ == "__main__":
    main()
