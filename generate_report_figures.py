"""
Generates publication-quality figures specifically sized and styled for the 4-page PDF report.
"""
import sqlite3
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.patches as patches

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
)

FIGURES_DIR = WORKSPACE_DIR / "report_figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def generate_figure1_location_map(output_path: Path = FIGURES_DIR / "fig1_location_map.png") -> None:
    """Generate geographic map schematic of Capitol Hill and the 1.5 km study zone."""
    fig, ax = plt.subplots(figsize=(8.5, 3.8), dpi=300)
    
    lat_c, lon_c = CENTER_LAT, CENTER_LON
    
    # 1.5 km in degrees approx
    d_lat = 1.5 / 111.19
    d_lon = 1.5 / 72.54
    
    # Bounding display limits
    pad_lon = 0.042
    pad_lat = 0.024
    ax.set_xlim(lon_c - pad_lon, lon_c + pad_lon)
    ax.set_ylim(lat_c - pad_lat, lat_c + pad_lat)
    
    # Draw Burrard Inlet water area (North of lat 49.293)
    x_water = np.linspace(lon_c - pad_lon, lon_c + pad_lon, 100)
    y_water = 49.293 + 0.003 * np.sin((x_water - lon_c) * 60)
    ax.fill_between(x_water, y_water, lat_c + pad_lat, color="#d0e1f9", alpha=0.85, label="Burrard Inlet (Waterway)")
    
    # Draw Land background
    ax.fill_between(x_water, lat_c - pad_lat, y_water, color="#f7f9f7", alpha=0.95)

    # Draw Fast Bounding Box
    bbox_rect = patches.Rectangle(
        (BBOX_LON_MIN, BBOX_LAT_MIN),
        BBOX_LON_MAX - BBOX_LON_MIN,
        BBOX_LAT_MAX - BBOX_LAT_MIN,
        linewidth=1.6,
        edgecolor="#0288d1",
        facecolor="#e1f5fe",
        alpha=0.35,
        linestyle="--",
        label=f"Fast Bounding Box ({BBOX_LAT_MIN:.3f}–{BBOX_LAT_MAX:.3f}°N)",
    )
    ax.add_patch(bbox_rect)

    # Draw Exact 1.5 km Radius Geodesic Circle
    circle = patches.Ellipse(
        (lon_c, lat_c),
        width=d_lon * 2,
        height=d_lat * 2,
        edgecolor="#d32f2f",
        facecolor="#ffebee",
        alpha=0.55,
        linewidth=2.2,
        label=f"1.5 km Geodesic Study Zone (Center: {lat_c}°N, {abs(lon_c)}°W)",
    )
    ax.add_patch(circle)

    # Center Target Point (Capitol Hill Summit)
    ax.plot(lon_c, lat_c, marker="*", color="#d32f2f", markersize=14, markeredgecolor="black", zorder=10)
    ax.text(lon_c + 0.002, lat_c + 0.0012, "Capitol Hill Center\n(Elev. ~115 m)", fontsize=8.5, fontweight="bold", color="#b71c1c", zorder=11)

    # Landmarks & Flight Paths
    ax.text(lon_c - 0.035, 49.298, "Burrard Inlet / Floatplane Route", fontsize=8, fontstyle="italic", color="#01579b", fontweight="bold")
    ax.text(lon_c + 0.022, 49.279, "Burnaby Mountain / SFU\n(Elev. 370 m)", fontsize=8, color="#2e7d32", fontweight="bold")
    ax.text(lon_c - 0.038, 49.277, "Hastings St Corridor\n(Vancouver / Burnaby Border)", fontsize=7.5, color="#555555")
    
    # Flight corridor arrows
    ax.annotate(
        "Low-Altitude GA & Floatplanes",
        xy=(lon_c - 0.015, 49.296),
        xytext=(lon_c - 0.036, 49.303),
        arrowprops=dict(facecolor="#0288d1", edgecolor="black", arrowstyle="->", lw=1.5),
        fontsize=8,
        fontweight="bold",
        color="#01579b",
    )
    ax.annotate(
        "Commercial Arrivals / Departures\n(5,000–9,000 ft via YVR East Corridors)",
        xy=(lon_c + 0.005, 49.283),
        xytext=(lon_c + 0.012, 49.270),
        arrowprops=dict(facecolor="#d9381e", edgecolor="black", arrowstyle="->", lw=1.5),
        fontsize=8,
        fontweight="bold",
        color="#b71c1c",
    )

    # Scale Bar (1 km)
    scale_km = 1.0
    scale_dlon = scale_km / 72.54
    scale_x0 = lon_c - 0.038
    scale_y0 = lat_c - 0.021
    ax.plot([scale_x0, scale_x0 + scale_dlon], [scale_y0, scale_y0], color="black", lw=3)
    ax.plot([scale_x0, scale_x0], [scale_y0 - 0.0008, scale_y0 + 0.0008], color="black", lw=1.5)
    ax.plot([scale_x0 + scale_dlon, scale_x0 + scale_dlon], [scale_y0 - 0.0008, scale_y0 + 0.0008], color="black", lw=1.5)
    ax.text(scale_x0 + scale_dlon / 2, scale_y0 + 0.0012, "1.0 km Scale", ha="center", fontsize=8, fontweight="bold")

    # Format Axes without scientific notation
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: f"{abs(x):.2f}°W"))
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, pos: f"{y:.2f}°N"))
    ax.tick_params(axis="both", labelsize=8)

    # Styling
    ax.set_title("Geographic Target & Monitoring Boundary: Capitol Hill (Burnaby, BC)", fontsize=11, fontweight="bold", pad=10, color="#1c3d5a")
    ax.set_xlabel("Longitude", fontsize=9, fontweight="bold")
    ax.set_ylabel("Latitude", fontsize=9, fontweight="bold")
    ax.grid(True, linestyle=":", alpha=0.55)
    ax.legend(loc="upper right", fontsize=7.5, frameon=True, framealpha=0.92)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved Figure 1 to {output_path}")


def generate_figure5_fleet_breakdown(output_path: Path = FIGURES_DIR / "fig5_fleet_breakdown.png") -> None:
    """Generate detailed top aircraft fleet breakdown chart for Page 4."""
    conn = sqlite3.connect(DATABASE_PATH)
    df = pd.read_sql("""
    SELECT 
        CASE 
            WHEN type_code = 'DH8D' THEN 'Dash 8 Q400 (Jazz/WestJet Encore)'
            WHEN type_code = 'C172' THEN 'Cessna 172 Skyhawk (Flight Training)'
            WHEN type_code = 'B38M' THEN 'Boeing 737 MAX 8 (WestJet/Air Canada)'
            WHEN type_code = 'B738' THEN 'Boeing 737-800 (Airlines/Charters)'
            WHEN type_code = 'B789' THEN 'Boeing 787-9 Dreamliner (Long-Haul)'
            WHEN type_code = 'CRJ9' THEN 'Bombardier CRJ-900 (Regional Jet)'
            WHEN type_code = 'B190' THEN 'Beechcraft 1900D (Pacific Coastal)'
            WHEN type_code = 'B77W' THEN 'Boeing 777-300ER (Widebody)'
            WHEN type_code = 'A321' THEN 'Airbus A321 (Air Canada/Delta)'
            WHEN type_code = 'A320' THEN 'Airbus A320 (Commercial Transport)'
            WHEN type_code = 'BCS3' THEN 'Airbus A220-300 (Air Canada/Delta)'
            WHEN type_code = 'SF34' THEN 'Saab 340 (Pacific Coastal)'
            WHEN type_code = 'B350' THEN 'King Air 350 (Medevac/Charter)'
            WHEN type_code = 'A333' THEN 'Airbus A330-300 (Widebody)'
            WHEN type_code = 'R44' THEN 'Robinson R44 (Commercial Helicopter)'
            ELSE type_code
        END as aircraft_label,
        type_code,
        count(*) as flight_count
    FROM flights
    WHERE date <= '2026-08-31' AND type_code IS NOT NULL AND type_code != ''
    GROUP BY type_code
    ORDER BY flight_count DESC
    LIMIT 14
    """, conn)
    conn.close()

    fig, ax = plt.subplots(figsize=(8.5, 3.2), dpi=300)
    
    # Sort for horizontal bar chart
    df = df.sort_values("flight_count", ascending=True)
    
    # Color palette
    colors = []
    for t in df["type_code"]:
        if t in ["DH8D", "CRJ9"]:
            colors.append("#1976d2") # Regional turboprop/jet
        elif t in ["C172", "R44", "B350"]:
            colors.append("#388e3c") # GA / Training
        elif t.startswith("B7") or t.startswith("B3"):
            colors.append("#d32f2f") # Boeing
        elif t.startswith("A3") or t.startswith("BCS"):
            colors.append("#f57c00") # Airbus
        else:
            colors.append("#7b1fa2")

    bars = ax.barh(df["aircraft_label"], df["flight_count"], color=colors, edgecolor="black", linewidth=0.7, height=0.68)
    
    # Annotate bar values
    max_val = df["flight_count"].max()
    for bar in bars:
        w = bar.get_width()
        ax.text(w + max_val * 0.015, bar.get_y() + bar.get_height() / 2, f"{w:,}", va="center", fontsize=7.5, fontweight="bold", color="#1c3d5a")

    ax.set_xlim(0, max_val * 1.15)
    ax.set_title("Top 14 Aircraft Types Detected in Capitol Hill Airspace (Jan 2025 – Aug 2026)", fontsize=10, fontweight="bold", pad=8, color="#1c3d5a")
    ax.set_xlabel("Total Overflights Count", fontsize=8, fontweight="bold")
    ax.grid(True, linestyle=":", alpha=0.5, axis="x")
    ax.tick_params(axis="y", labelsize=7.5)
    ax.tick_params(axis="x", labelsize=7.5)

    # Custom category legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#1976d2", label="Regional Turboprop / Jet"),
        Patch(facecolor="#d32f2f", label="Boeing Air Transports"),
        Patch(facecolor="#f57c00", label="Airbus Air Transports"),
        Patch(facecolor="#388e3c", label="General Aviation / Helicopters"),
    ]
    ax.legend(handles=legend_elements, loc="lower right", fontsize=7.0, framealpha=0.95)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved Figure 5 to {output_path}")


if __name__ == "__main__":
    generate_figure1_location_map()
    generate_figure5_fleet_breakdown()
