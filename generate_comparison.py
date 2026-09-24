import sqlite3
import json
import math
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DB_PATH = Path("regional_vancouver_flights.db")
CAPITOL_HILL = (49.2869, -122.9853)
LAT_MIN, LAT_MAX = 49.10, 49.40
LON_MIN, LON_MAX = -123.35, -122.50

def draw_coastal_features(ax):
    ax.set_facecolor("#111111")
    inlet_x = [-123.35, -123.35, -123.15, -123.10, -122.95, -122.82, -122.82, -122.95, -123.12, -123.25, -123.35]
    inlet_y = [49.40,   49.32,   49.30,   49.29,   49.29,   49.28,   49.32,   49.31,   49.31,   49.33,   49.40]
    ax.fill(inlet_x, inlet_y, color="#1c2833", zorder=1)
    strait_x = [-123.35, -123.25, -123.20, -123.20, -123.35]
    strait_y = [49.10,   49.10,   49.18,   49.27,   49.27]
    ax.fill(strait_x, strait_y, color="#1c2833", zorder=1)
    ax.plot([-123.20, -123.15], [49.195, 49.195], color="#888888", lw=2.0, zorder=10)
    ax.plot(CAPITOL_HILL[1], CAPITOL_HILL[0], "w*", ms=5, zorder=15)

def fetch_data(periods, limit_days=None):
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    
    data = {}
    for period in periods:
        query = f"SELECT date, is_arrival, trajectory_json FROM regional_flights WHERE period='{period}'"
        c.execute(query)
        rows = c.fetchall()
        
        if limit_days:
            # only use first `limit_days` dates
            dates = sorted(list(set([r[0] for r in rows])))[:limit_days]
            rows = [r for r in rows if r[0] in dates]
            
        cat_data = {
            "Local/Low": {"trajs": [], "color": "#00ffcc", "title": "Local/Low"},
            "Arrivals26": {"trajs": [], "color": "#ff3366", "title": "YVR Arr 26L/R"},
            "Arrivals8": {"trajs": [], "color": "#3399ff", "title": "YVR Arr 8L/R"},
            "Departures": {"trajs": [], "color": "#ffcc00", "title": "YVR Dep"}
        }
        
        for row in rows:
            date, is_arrival, traj = row
            pts = json.loads(traj)
            if not pts: continue
            
            first_alt = pts[0][2] if pts[0][2] is not None else 0
            last_alt = pts[-1][2] if pts[-1][2] is not None else 0
            max_alt = max([p[2] for p in pts if len(p)>2 and p[2] is not None] + [0])
            app_trk = -1
            for p in reversed(pts):
                if p[2] is not None and 200 <= p[2] <= 4000 and p[3] is not None:
                    app_trk = p[3]
                    break
            final_trk = app_trk if app_trk != -1 else (pts[-1][3] if pts[-1][3] is not None else -1)
            
            cat = None
            if max_alt < 5000:
                cat = "Local/Low"
            elif (last_alt - first_alt) > 2000 and first_alt < 5000:
                cat = "Departures"
            elif is_arrival:
                if 180 <= final_trk <= 360:
                    cat = "Arrivals26"
                elif 0 <= final_trk < 180:
                    cat = "Arrivals8"
                    
            if cat:
                cat_data[cat]["trajs"].append(pts)
        
        data[period] = cat_data
        
    conn.close()
    return data

def plot_comparison(data, period1, period2, title, out_filename):
    fig, axes = plt.subplots(2, 4, figsize=(16, 9), sharex=True, sharey=True)
    fig.patch.set_facecolor('#ffffff')
    
    plot_order = ["Local/Low", "Arrivals26", "Arrivals8", "Departures"]
    
    for i, period in enumerate([period1, period2]):
        for j, cat in enumerate(plot_order):
            ax = axes[i, j]
            draw_coastal_features(ax)
            ax.set_xlim(LON_MIN, LON_MAX)
            ax.set_ylim(LAT_MIN, LAT_MAX)
            
            pdata = data[period][cat]
            color = pdata["color"]
            alpha = 0.15 if len(pdata["trajs"]) < 500 else 0.05
            
            for pts in pdata["trajs"]:
                lats = [p[0] for p in pts]
                lons = [p[1] for p in pts]
                ax.plot(lons, lats, color=color, alpha=alpha, lw=0.8, zorder=5)
                
            ax.set_title(f"{period.upper()}: {pdata['title']}", color="black", fontweight="bold", fontsize=10)
            ax.set_xticks([])
            ax.set_yticks([])
            
    plt.suptitle(title, color="black", fontweight="bold", fontsize=14)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(Path("figures") / out_filename, dpi=300)
    plt.close()

if __name__ == "__main__":
    # Wait for oct2025 and dec2025 to finish extracting first!
    pass
