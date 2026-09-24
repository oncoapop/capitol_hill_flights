import sqlite3
import json
import math
import csv

EARTH_RADIUS_KM = 6371.0088
YVR_LAT, YVR_LON = 49.1939, -123.1844
CAPITOL_HILL = (49.2869, -122.9853)

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

conn = sqlite3.connect("regional_vancouver_flights.db")
c = conn.cursor()

def process_period(period):
    c.execute(f"SELECT is_arrival, trajectory_json FROM regional_flights WHERE period='{period}' AND crosses_capitol_hill=1")
    rows = c.fetchall()
    
    counts = {
        "arr26": 0,
        "arr8": 0,
        "dep": 0,
        "overflights": 0,
        "total": 0
    }
    
    for r in rows:
        is_arrival, traj = r
        pts = json.loads(traj)
        if not pts: continue
        
        counts["total"] += 1
        
        first_pt, last_pt = pts[0], pts[-1]
        first_alt = first_pt[2] if first_pt[2] is not None else 0
        last_alt = last_pt[2] if last_pt[2] is not None else 0
        
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
        
        if is_verified_yvr:
            if is_yvr_dep:
                counts["dep"] += 1
            elif is_arrival:
                if 180 <= final_trk <= 360:
                    counts["arr26"] += 1
                elif 0 <= final_trk < 180:
                    counts["arr8"] += 1
                else:
                    counts["overflights"] += 1 # Edge case heading
            else:
                counts["overflights"] += 1
        else:
            counts["overflights"] += 1
            
    return counts

stats25 = process_period('aug2025')
stats26 = process_period('aug2026')

labels = [
    ("YVR Arrivals 26L/R", "arr26"),
    ("YVR Arrivals 8L/R", "arr8"),
    ("YVR Departures", "dep"),
    ("Overflights (Non-YVR / Local)", "overflights")
]

with open("capitol_hill_all_traffic.csv", "w", newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["Traffic Category Over Capitol Hill", "August 2025", "% of Total Over Capitol Hill", "August 2026", "% of Total Over Capitol Hill"])
    
    for label, key in labels:
        v25 = stats25[key]
        p25 = f"{(v25 / stats25['total']) * 100:.1f}%" if stats25['total'] > 0 else "0.0%"
        v26 = stats26[key]
        p26 = f"{(v26 / stats26['total']) * 100:.1f}%" if stats26['total'] > 0 else "0.0%"
        writer.writerow([label, v25, p25, v26, p26])
        
    writer.writerow(["TOTAL Flights Over Capitol Hill", stats25['total'], "100%", stats26['total'], "100%"])

