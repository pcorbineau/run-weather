from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID", "")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET", "")
STRAVA_REDIRECT_URI = "http://localhost:8000/auth/callback"

OUTPUTS_DIR = BASE_DIR / "outputs"
CACHE_DIR = BASE_DIR / "cache"

CACHE_TTL_DAYS = 30
OPEN_METEO_BASE_URL = "https://archive-api.open-meteo.com/v1/archive"
