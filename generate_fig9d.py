import sqlite3
import json
import math
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import csv

DB_PATH = Path("regional_vancouver_flights.db")
CAPITOL_HILL = (49.2869, -122.9853)
LAT_MIN, LAT_MAX = 49.10, 49.40
LON_MIN, LON_MAX = -123.35, -122.50
EARTH_RADIUS_KM = 6371.0088
YVR_LAT, YVR_LON = 49.1939, -123.1844

def haversine_km(lat1, lon1, lat2, lon2):
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2.0)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2.0)**2
    return 2.0 * EARTH_RADIUS_KM * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

def calculate_initial_compass_bearing(pointA, pointB):
    lat1, lat2 = math.radians(pointA[0]), math.radians(pointB[0])
    diffLong = math.radians(pointB[1] - pointA[1])
    x = math.sin(diffLong) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(diffLong))
    initial_bearing = math.atan2(x, y)
    return (math.degrees(initial_bearing) + 360) % 360

def angle_diff(a, b):
    diff = abs(a - b) % 360
    return diff if diff <= 180 else 360 - diff

def is_on_certified_yvr_runway(lat, lon, alt):
    if alt is None or alt > 1000: return False
    if 49.198 <= lat <= 49.207 and -123.205 <= lon <= -123.140: return True
    if 49.178 <= lat <= 49.187 and -123.205 <= lon <= -123.130: return True
    if 49.185 <= lat <= 49.195 and -123.185 <= lon <= -123.170: return True
    return False

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

def fetch_data(periods):
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    data = {}
    for period in periods:
        query = f"SELECT is_arrival, trajectory_json FROM regional_flights WHERE period='{period}'"
        c.execute(query)
        rows = c.fetchall()
        
        cat_data = {
            "Local/Low": {"trajs": [], "color": "#00ffcc", "title": "Local/Low"},
            "Arrivals26": {"trajs": [], "color": "#ff3366", "title": "YVR Arr 26L/R"},
            "Arrivals8": {"trajs": [], "color": "#3399ff", "title": "YVR Arr 8L/R"},
            "Departures": {"trajs": [], "color": "#ffcc00", "title": "YVR Dep"},
            "Overflights": {"trajs": [], "color": "#aa33ff", "title": "Overflights"}
        }
        
        total_tracked = 0
        
        for row in rows:
            is_arrival, traj = row
            pts = json.loads(traj)
            if not pts: continue
            
            total_tracked += 1
            
            first_pt, last_pt = pts[0], pts[-1]
            first_alt = first_pt[2] if first_pt[2] is not None else 0
            last_alt = last_pt[2] if last_pt[2] is not None else 0
            max_alt = max([p[2] for p in pts if len(p)>2 and p[2] is not None] + [0])
            
            first_trk = first_pt[3] if first_pt[3] is not None else -1
            app_trk = -1
            for p in reversed(pts):
                if p[2] is not None and 200 <= p[2] <= 4000 and p[3] is not None:
                    app_trk = p[3]
                    break
            final_trk = app_trk if app_trk != -1 else (last_pt[3] if last_pt[3] is not None else -1)
            
            is_yvr_dep = ((last_alt - first_alt) > 2000 and first_alt < 5000)
            
            touches_runway = False
            for p in pts:
                if is_on_certified_yvr_runway(p[0], p[1], p[2]):
                    touches_runway = True
                    break
                    
            heading_to_yvr = False
            if is_arrival and last_alt < 5000 and final_trk != -1:
                bearing_to = calculate_initial_compass_bearing((last_pt[0], last_pt[1]), (YVR_LAT, YVR_LON))
                dist = haversine_km(last_pt[0], last_pt[1], YVR_LAT, YVR_LON)
                if angle_diff(final_trk, bearing_to) <= 35 and dist < 35:
                    heading_to_yvr = True
                    
            coming_from_yvr = False
            if is_yvr_dep and first_alt < 5000 and first_trk != -1:
                bearing_from = calculate_initial_compass_bearing((YVR_LAT, YVR_LON), (first_pt[0], first_pt[1]))
                dist = haversine_km(first_pt[0], first_pt[1], YVR_LAT, YVR_LON)
                if angle_diff(first_trk, bearing_from) <= 35 and dist < 35:
                    coming_from_yvr = True
            
            is_verified_yvr = touches_runway or heading_to_yvr or coming_from_yvr
            
            cat = None
            if max_alt < 5000 and not is_verified_yvr:
                cat = "Local/Low"
            elif is_verified_yvr:
                if max_alt < 5000:
                    cat = "Local/Low"
                elif is_yvr_dep:
                    cat = "Departures"
                elif is_arrival:
                    if 180 <= final_trk <= 360:
                        cat = "Arrivals26"
                    elif 0 <= final_trk < 180:
                        cat = "Arrivals8"
            else:
                cat = "Overflights"
            
            if cat:
                cat_data[cat]["trajs"].append(pts)
        
        data[period] = {"cats": cat_data, "total": total_tracked}
        
    conn.close()
    return data

data = fetch_data(['aug2025', 'aug2026'])

fig, axes = plt.subplots(2, 5, figsize=(20, 9), sharex=True, sharey=True)
fig.patch.set_facecolor('#ffffff')
plot_order = ["Local/Low", "Arrivals26", "Arrivals8", "Departures", "Overflights"]

for i, period in enumerate(['aug2025', 'aug2026']):
    for j, cat in enumerate(plot_order):
        ax = axes[i, j]
        draw_coastal_features(ax)
        ax.set_xlim(LON_MIN, LON_MAX)
        ax.set_ylim(LAT_MIN, LAT_MAX)
        pdata = data[period]["cats"][cat]
        color = pdata["color"]
        alpha = 0.15 if len(pdata["trajs"]) < 500 else 0.05
        for pts in pdata["trajs"]:
            lats = [p[0] for p in pts]
            lons = [p[1] for p in pts]
            ax.plot(lons, lats, color=color, alpha=alpha, lw=0.8, zorder=5)
            
        title_str = f"{period.upper()}: {pdata['title']}"
        ax.set_title(title_str, color="black", fontweight="bold", fontsize=10)
        ax.set_xticks([])
        ax.set_yticks([])
        
        # Add N count to the box
        count = len(pdata["trajs"])
        ax.text(0.05, 0.05, f"N={count}", transform=ax.transAxes, color="white", fontsize=12, fontweight="bold", zorder=20)

plt.suptitle("Figure 9d: Metro Vancouver Traffic Composition with Overflights Control (Aug 2025 vs 2026)", color="black", fontweight="bold", fontsize=14)
plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig(Path("figures") / "fig9d_comparison.png", dpi=300)
plt.close()

labels = [
    ("Local / Low (<5,000 ft)", "Local/Low"),
    ("YVR Arrivals 26L/R", "Arrivals26"),
    ("YVR Arrivals 8L/R", "Arrivals8"),
    ("YVR Departures", "Departures"),
    ("Non-YVR Overflights", "Overflights"),
    ("Total Tracked Flights in Region (Control)", "Total")
]

with open("/Users/dyap/.gemini/antigravity/brain/374baa36-bf25-4588-8119-c1c3cdb00b2c/fig9d_data.csv", "w", newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["Figure 9d Panel Category", "August 2025", "% of Regional Total", "August 2026", "% of Regional Total"])
    
    total25 = data['aug2025']["total"]
    total26 = data['aug2026']["total"]
    
    for label, key in labels:
        if key == "Total":
            v25 = total25
            v26 = total26
            p25 = "100%"
            p26 = "100%"
        else:
            v25 = len(data['aug2025']["cats"][key]['trajs'])
            v26 = len(data['aug2026']["cats"][key]['trajs'])
            p25 = f"{(v25 / total25) * 100:.1f}%"
            p26 = f"{(v26 / total26) * 100:.1f}%"
            
        writer.writerow([label, v25, p25, v26, p26])
