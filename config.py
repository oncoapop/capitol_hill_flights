"""
Configuration settings for Capitol Hill, Burnaby, BC aircraft overflight pipeline.
"""
from pathlib import Path

# Target Location: Capitol Hill, Burnaby, BC, Canada
CENTER_LAT = 49.2869
CENTER_LON = -122.9853
RADIUS_KM = 1.5
RADIUS_METERS = 1500.0

# Fast Bounding Box
BBOX_LAT_MIN = 49.2734
BBOX_LAT_MAX = 49.3004
BBOX_LON_MIN = -123.0060
BBOX_LON_MAX = -122.9646

# Workspace & File Paths
WORKSPACE_DIR = Path(__file__).parent.resolve()
DATABASE_PATH = WORKSPACE_DIR / "capitol_hill_flights.db"
OUTPUT_DIR = WORKSPACE_DIR / "exports"
HEATMAP_IMAGE_PATH = WORKSPACE_DIR / "flight_density_heatmap.png"

# GitHub Archive Repositories
REPOS = {
    2025: "adsblol/globe_history_2025",
    2026: "adsblol/globe_history_2026",
}

GITHUB_API_BASE = "https://api.github.com/repos"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ADS-B Capitol Hill Flight Tracker"

# Timezones
LOCAL_TIMEZONE = "America/Vancouver"
