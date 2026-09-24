import sqlite3
import json
import math
import csv

EARTH_RADIUS_KM = 6371.0088
YVR_LAT = 49.1939
YVR_LON = -123.1844

def haversine_km(lat1, lon1, lat2, lon2):
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2.0)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2.0)**2
    return 2.0 * EARTH_RADIUS_KM * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

def calculate_initial_compass_bearing(pointA, pointB):
    lat1 = math.radians(pointA[0])
    lat2 = math.radians(pointB[0])
    diffLong = math.radians(pointB[1] - pointA[1])
    x = math.sin(diffLong) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(diffLong))
    initial_bearing = math.atan2(x, y)
    initial_bearing = math.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360
    return compass_bearing

def angle_diff(a, b):
    diff = abs(a - b) % 360
    return diff if diff <= 180 else 360 - diff

def is_on_certified_yvr_runway(lat, lon, alt):
    if alt is None or alt > 1000: return False
    if 49.198 <= lat <= 49.207 and -123.205 <= lon <= -123.140: return True
    if 49.178 <= lat <= 49.187 and -123.205 <= lon <= -123.130: return True
    if 49.185 <= lat <= 49.195 and -123.185 <= lon <= -123.170: return True
    return False

conn = sqlite3.connect("regional_vancouver_flights.db")
c = conn.cursor()

def get_stats(period):
    c.execute(f"SELECT is_arrival, trajectory_json, crosses_capitol_hill FROM regional_flights WHERE period='{period}'")
    rows = c.fetchall()
    
    total_yvr_regional = 0
    ch_counts = {"arr26": 0, "arr8": 0, "dep": 0, "other": 0} 
    total_ch_yvr = 0
    
    for is_arrival, traj, crosses_ch in rows:
        pts = json.loads(traj)
        if not pts: continue
        
        touches_runway = False
        for p in pts:
            if is_on_certified_yvr_runway(p[0], p[1], p[2]):
                touches_runway = True
                break
                
        first_pt = pts[0]
        last_pt = pts[-1]
        first_alt = first_pt[2] if first_pt[2] is not None else 0
        last_alt = last_pt[2] if last_pt[2] is not None else 0
        first_trk = first_pt[3] if first_pt[3] is not None else -1
        app_trk = -1
        for p in reversed(pts):
            if p[2] is not None and 200 <= p[2] <= 4000 and p[3] is not None:
                app_trk = p[3]
                break
        final_trk = app_trk if app_trk != -1 else (last_pt[3] if last_pt[3] is not None else -1)
        
        is_yvr_dep_profile = ((last_alt - first_alt) > 2000 and first_alt < 5000)
        
        heading_to_yvr = False
        if is_arrival and last_alt < 5000 and final_trk != -1:
            bearing_to = calculate_initial_compass_bearing((last_pt[0], last_pt[1]), (YVR_LAT, YVR_LON))
            # Check if pointing at YVR (within 35 deg) and close enough (within 35 km)
            dist = haversine_km(last_pt[0], last_pt[1], YVR_LAT, YVR_LON)
            if angle_diff(final_trk, bearing_to) <= 35 and dist < 35:
                heading_to_yvr = True
                
        coming_from_yvr = False
        if is_yvr_dep_profile and first_alt < 5000 and first_trk != -1:
            bearing_from = calculate_initial_compass_bearing((YVR_LAT, YVR_LON), (first_pt[0], first_pt[1]))
            dist = haversine_km(first_pt[0], first_pt[1], YVR_LAT, YVR_LON)
            if angle_diff(first_trk, bearing_from) <= 35 and dist < 35:
                coming_from_yvr = True
                
        is_yvr_flight = touches_runway or heading_to_yvr or coming_from_yvr
        
        if not is_yvr_flight:
            continue
            
        total_yvr_regional += 1
        
        if crosses_ch:
            total_ch_yvr += 1
            if is_yvr_dep_profile:
                ch_counts["dep"] += 1
            elif is_arrival:
                if 180 <= final_trk <= 360:
                    ch_counts["arr26"] += 1
                elif 0 <= final_trk < 180:
                    ch_counts["arr8"] += 1
                else:
                    ch_counts["other"] += 1
            else:
                ch_counts["other"] += 1
                    
    return total_yvr_regional, total_ch_yvr, ch_counts

reg25, ch25, cats25 = get_stats("aug2025")
reg26, ch26, cats26 = get_stats("aug2026")

labels = [
    ("YVR Arrivals 26L/R over Capitol Hill", "arr26"),
    ("YVR Arrivals 8L/R over Capitol Hill", "arr8"),
    ("YVR Departures over Capitol Hill", "dep")
]

with open("yvr_extended_runway_capitol_hill.csv", "w", newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["Traffic Category (YVR Flights Extended)", "August 2025", "% of Total YVR Flights", "August 2026", "% of Total YVR Flights"])
    
    for label, key in labels:
        v25 = cats25[key]
        p25 = f"{(v25 / reg25) * 100:.1f}%" if reg25 > 0 else "0%"
        v26 = cats26[key]
        p26 = f"{(v26 / reg26) * 100:.1f}%" if reg26 > 0 else "0%"
        writer.writerow([label, v25, p25, v26, p26])
        
    writer.writerow(["Subtotal: YVR Flights over Capitol Hill", ch25, f"{(ch25 / reg25) * 100:.1f}%", ch26, f"{(ch26 / reg26) * 100:.1f}%"])
    writer.writerow(["CONTROL: Total YVR Flights Tracked in Region", reg25, "100%", reg26, "100%"])

md = """# Scientific Precision: YVR Operations Over Capitol Hill (Including ADSB Drop-offs)

This table recovers flights that dropped off ADSB coverage a few miles before touchdown. A flight is securely identified as a YVR flight if it either:
1. Physically registers a coordinate on a certified YVR runway (08L/R, 26L/R, 13/31) at < 1000 ft.
2. OR its final ADSB ping is < 5000 ft, within 35 km of YVR, and its heading is pointed directly at the YVR airfield (within a 35-degree tolerance).
3. OR its first ADSB ping is < 5000 ft, within 35 km of YVR, and its heading is pointed directly away from the YVR airfield.

| Traffic Category (YVR Flights Extended) | August 2025 | % of Total YVR Flights | August 2026 | % of Total YVR Flights |
| :--- | :--- | :--- | :--- | :--- |
"""
for label, key in labels:
    v25 = cats25[key]
    p25 = f"{(v25 / reg25) * 100:.1f}%" if reg25 > 0 else "0%"
    v26 = cats26[key]
    p26 = f"{(v26 / reg26) * 100:.1f}%" if reg26 > 0 else "0%"
    md += f"| {label} | {v25:,} | {p25} | {v26:,} | {p26} |\n"
    
md += f"| **Subtotal: YVR Flights over Capitol Hill** | **{ch25:,}** | **{(ch25 / reg25) * 100:.1f}%** | **{ch26:,}** | **{(ch26 / reg26) * 100:.1f}%** |\n"
md += f"| **CONTROL: Total YVR Flights Tracked in Region** | **{reg25:,}** | **100%** | **{reg26:,}** | **100%** |\n"

with open("/Users/dyap/.gemini/antigravity/brain/374baa36-bf25-4588-8119-c1c3cdb00b2c/table_yvr_extended_runway.md", "w") as f:
    f.write(md)
    
