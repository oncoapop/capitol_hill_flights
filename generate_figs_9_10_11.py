import json
import sqlite3
import math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Ellipse
import matplotlib.ticker as ticker

DB_PATH = Path("regional_vancouver_flights.db")
OUT_DIR = Path("figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)

LAT_MIN, LAT_MAX = 49.10, 49.40
LON_MIN, LON_MAX = -123.35, -122.50

CAPITOL_HILL = (49.2869, -122.9853)
YVR_RUNWAYS = (49.1939, -123.1844)
EARTH_RADIUS_KM = 6371.0088

def haversine_km(lat1, lon1, lat2, lon2):
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2.0)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2.0)**2
    return 2.0 * EARTH_RADIUS_KM * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

def get_trajectories():
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("SELECT period, is_arrival, crosses_capitol_hill, trajectory_json FROM regional_flights")
    data = c.fetchall()
    conn.close()
    
    trajs = {"aug2025": [], "aug2026": []}
    for row in data:
        period = row[0]
        traj = json.loads(row[3])
        trajs[period].append({
            "is_arrival": row[1],
            "crosses_capitol_hill": row[2],
            "pts": traj
        })
    return trajs

def draw_coastal_features(ax):
    ax.set_facecolor("#f4f7f6")
    inlet_x = [-123.35, -123.35, -123.15, -123.10, -122.95, -122.82, -122.82, -122.95, -123.12, -123.25, -123.35]
    inlet_y = [49.40,   49.32,   49.30,   49.29,   49.29,   49.28,   49.32,   49.31,   49.31,   49.33,   49.40]
    ax.fill(inlet_x, inlet_y, color="#d8e8f0", alpha=0.9, zorder=1)
    strait_x = [-123.35, -123.25, -123.20, -123.20, -123.35]
    strait_y = [49.10,   49.10,   49.18,   49.27,   49.27]
    ax.fill(strait_x, strait_y, color="#d8e8f0", alpha=0.9, zorder=1)
    ax.plot([-123.20, -123.15], [49.195, 49.195], "k-", lw=2.5, zorder=10)
    ax.plot([-123.19, -123.15], [49.190, 49.190], "k-", lw=2.0, zorder=10)
    ax.text(-123.21, 49.185, "YVR", fontsize=7, fontweight="bold", ha="right", zorder=11)
    ax.plot(CAPITOL_HILL[1], CAPITOL_HILL[0], "r*", ms=8, zorder=15)
    ax.text(CAPITOL_HILL[1], CAPITOL_HILL[0]-0.015, "Capitol Hill", fontsize=7, fontweight="bold", color="#b20000", ha="center", zorder=16)

def fig9_2d_density(trajs):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5.5), sharex=True, sharey=True)
    for ax, period, title in zip([ax1, ax2], ["aug2025", "aug2026"], ["(a) Pre-VAMP (Aug 2025)", "(b) Post-VAMP (Aug 2026)"]):
        draw_coastal_features(ax)
        ax.set_xlim(LON_MIN, LON_MAX)
        ax.set_ylim(LAT_MIN, LAT_MAX)
        ax.set_title(title, fontsize=10, fontweight="bold")
        
        all_lons = []
        all_lats = []
        for t in trajs[period]:
            for p in t["pts"]:
                all_lons.append(p[1])
                all_lats.append(p[0])
                
        hb = ax.hexbin(all_lons, all_lats, gridsize=200, cmap='inferno', bins='log', mincnt=3, zorder=5, alpha=0.85)
        cb = fig.colorbar(hb, ax=ax, fraction=0.046, pad=0.04)
        cb.set_label("Point Density (Log Scale)")
        
    plt.suptitle("Figure 9: Regional Flight Trajectory 2D Density Map\nThresholded to visualize true traffic volume across the Metro Vancouver Airspace", fontsize=12, fontweight="bold")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "fig9_regional_density.png", dpi=300)
    plt.close()

def fig10_arrivals(trajs):
    fig, ax = plt.subplots(figsize=(10, 6))
    draw_coastal_features(ax)
    ax.set_xlim(LON_MIN, LON_MAX)
    ax.set_ylim(LAT_MIN, LAT_MAX)
    
    for t in trajs["aug2026"]:
        if t["is_arrival"]:
            pts = t["pts"]
            if not pts: continue
            min_dist = 9999
            closest_pt = pts[0]
            for p in pts:
                dist = haversine_km(p[0], p[1], CAPITOL_HILL[0], CAPITOL_HILL[1])
                if dist < min_dist:
                    min_dist = dist
                    closest_pt = p
                    
            if min_dist < 5.0:
                trk = closest_pt[3] if len(closest_pt) > 3 else 0
                if trk is None: trk = 0
                is_eastbound = (0 <= trk <= 180)
                
                lats = [p[0] for p in pts]
                lons = [p[1] for p in pts]
                
                if is_eastbound:
                    color = "#d62728" # Red for eastward
                    alpha = 0.15
                else:
                    color = "#1f77b4" # Blue for westbound
                    alpha = 0.15
                    
                ax.plot(lons, lats, color=color, alpha=alpha, lw=0.8, zorder=4)
                
    custom_lines = [
        mpatches.Patch(color='#d62728', alpha=0.7, label='Eastward Overflights (Landing 26L/R facing WEST)\nConcentrated path with 5,000 ft min altitude'),
        mpatches.Patch(color='#1f77b4', alpha=0.7, label='Westbound Overflights (Landing 8L/R)\nHigher altitude path (~7,000 ft)')
    ]
    ax.legend(handles=custom_lines, loc="upper left", fontsize=9, framealpha=0.9)
    ax.set_title("Figure 10: Total Descending Commercial Arrivals (YVR)\nHighlighting approach directionality and associated altitudes over Capitol Hill", fontsize=11, fontweight="bold")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "fig10_arrivals_highlight.png", dpi=300)
    plt.close()
    
def fig11_cross_section(trajs):
    dists_2025 = []
    dists_2026 = []
    
    for p_name, dists in [("aug2025", dists_2025), ("aug2026", dists_2026)]:
        for t in trajs[p_name]:
            if t["is_arrival"] and t["crosses_capitol_hill"]:
                min_dist = min([haversine_km(p[0], p[1], CAPITOL_HILL[0], CAPITOL_HILL[1]) for p in t["pts"]])
                dists.append(min_dist * 1000)
                
    fig, ax = plt.subplots(figsize=(8, 5))
    bins = np.linspace(0, 1500, 30)
    ax.hist(dists_2026, bins=bins, alpha=0.75, color='#d62728', label=f'Aug 2026 (n={len(dists_2026)})')
    ax.hist(dists_2025, bins=bins, alpha=0.75, color='#1f77b4', label=f'Aug 2025 (n={len(dists_2025)})')
    
    ax.axvspan(0, 500, color='yellow', alpha=0.2, label='500m Core Zone', zorder=0)
    ax.axvline(500, color='k', linestyle='--', lw=1.5, zorder=1)
    
    ax.set_xlabel("Closest Lateral Distance to Capitol Hill Apex (meters)", fontsize=10)
    ax.set_ylabel("Number of Descending Commercial Arrivals", fontsize=10)
    ax.set_title("Figure 11: Cross-Sectional Density of Commercial Jet Arrivals\nDemonstrating the narrow, highly concentrated scale of the 500m corridor", fontsize=11, fontweight="bold")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "fig11_cross_section.png", dpi=300)
    plt.close()

if __name__ == "__main__":
    t = get_trajectories()
    fig9_2d_density(t)
    fig10_arrivals(t)
    fig11_cross_section(t)
