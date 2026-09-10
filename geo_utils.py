"""
Geographic calculations, bounding box filtering, and flight trace processing.
"""
import math
import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Optional, Dict, Any, List

from config import (
    CENTER_LAT,
    CENTER_LON,
    RADIUS_KM,
    BBOX_LAT_MIN,
    BBOX_LAT_MAX,
    BBOX_LON_MIN,
    BBOX_LON_MAX,
    LOCAL_TIMEZONE,
)

EARTH_RADIUS_KM = 6371.0088


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth in kilometers.
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    sin_dphi = math.sin(delta_phi / 2.0)
    sin_dlambda = math.sin(delta_lambda / 2.0)

    a = sin_dphi * sin_dphi + math.cos(phi1) * math.cos(phi2) * sin_dlambda * sin_dlambda
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return EARTH_RADIUS_KM * c


def in_bounding_box(
    lat: float,
    lon: float,
    min_lat: float = BBOX_LAT_MIN,
    max_lat: float = BBOX_LAT_MAX,
    min_lon: float = BBOX_LON_MIN,
    max_lon: float = BBOX_LON_MAX,
) -> bool:
    """
    Fast rectangular bounding box check.
    """
    return (min_lat <= lat <= max_lat) and (min_lon <= lon <= max_lon)


def process_trace_data(
    raw_data: Dict[str, Any],
    date_str: str,
    center_lat: float = CENTER_LAT,
    center_lon: float = CENTER_LON,
    radius_km: float = RADIUS_KM,
) -> Optional[Dict[str, Any]]:
    """
    Process a single aircraft readsb trace JSON.
    Returns structured flight summary dict if the flight passed within radius_km of center,
    or None otherwise.
    """
    trace = raw_data.get("trace", [])
    if not trace:
        return None

    base_timestamp = raw_data.get("timestamp", 0.0)
    icao = raw_data.get("icao", "").strip().upper()
    callsign = (raw_data.get("flight") or "").strip().upper() or None
    registration = (raw_data.get("r") or "").strip() or None
    type_code = (raw_data.get("t") or "").strip() or None
    type_desc = (raw_data.get("desc") or "").strip() or None

    matched_points: List[Dict[str, Any]] = []

    for point in trace:
        # readsb trace format:
        # [0:time_offset, 1:lat, 2:lon, 3:alt_baro, 4:gs, 5:track, 6:geom_rate/flags, 7:squawk, ...]
        if len(point) < 3:
            continue

        lat = point[1]
        lon = point[2]

        if lat is None or lon is None:
            continue

        # Fast bounding box pre-filter
        if not in_bounding_box(lat, lon):
            continue

        # Precise distance calculation
        dist = haversine_distance_km(lat, lon, center_lat, center_lon)
        if dist <= radius_km:
            time_offset = point[0] if point[0] is not None else 0.0
            point_ts = base_timestamp + time_offset
            alt_baro = point[3] if len(point) > 3 else None
            gs = point[4] if len(point) > 4 else None
            track = point[5] if len(point) > 5 else None
            alt_geom = point[10] if len(point) > 10 else None

            matched_points.append({
                "timestamp": point_ts,
                "lat": round(lat, 6),
                "lon": round(lon, 6),
                "dist_km": round(dist, 4),
                "alt_baro": alt_baro,
                "alt_geom": alt_geom,
                "gs": gs,
                "track": track,
            })

    if not matched_points:
        return None

    # Sort matched points by timestamp
    matched_points.sort(key=lambda p: p["timestamp"])

    # Find closest point of approach (CPA)
    cpa_point = min(matched_points, key=lambda p: p["dist_km"])

    first_seen_ts = matched_points[0]["timestamp"]
    last_seen_ts = matched_points[-1]["timestamp"]

    # Generate ISO strings for UTC and Local
    tz_local = ZoneInfo(LOCAL_TIMEZONE)
    first_seen_utc = datetime.fromtimestamp(first_seen_ts, tz=timezone.utc).isoformat()
    last_seen_utc = datetime.fromtimestamp(last_seen_ts, tz=timezone.utc).isoformat()
    cpa_utc = datetime.fromtimestamp(cpa_point["timestamp"], tz=timezone.utc).isoformat()
    cpa_local = datetime.fromtimestamp(cpa_point["timestamp"], tz=timezone.utc).astimezone(tz_local).isoformat()
    cpa_hour_local = datetime.fromtimestamp(cpa_point["timestamp"], tz=timezone.utc).astimezone(tz_local).hour
    cpa_hour_utc = datetime.fromtimestamp(cpa_point["timestamp"], tz=timezone.utc).hour

    return {
        "date": date_str,
        "icao": icao,
        "callsign": callsign,
        "registration": registration,
        "type_code": type_code,
        "type_desc": type_desc,
        "first_seen_ts": first_seen_ts,
        "last_seen_ts": last_seen_ts,
        "first_seen_utc": first_seen_utc,
        "last_seen_utc": last_seen_utc,
        "cpa_ts": cpa_point["timestamp"],
        "cpa_utc": cpa_utc,
        "cpa_local": cpa_local,
        "cpa_hour_local": cpa_hour_local,
        "cpa_hour_utc": cpa_hour_utc,
        "min_dist_km": cpa_point["dist_km"],
        "min_dist_alt_baro": str(cpa_point["alt_baro"]) if cpa_point["alt_baro"] is not None else None,
        "min_dist_gs": cpa_point["gs"],
        "min_dist_track": cpa_point["track"],
        "min_dist_lat": cpa_point["lat"],
        "min_dist_lon": cpa_point["lon"],
        "num_points_in_zone": len(matched_points),
        "total_trace_points": len(trace),
        "matched_points_json": json.dumps(matched_points),
    }
