"""
Bot Configuration and Settings Loader
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CHARTS_DIR = BASE_DIR / "charts"

# Ensure runtime directories exist
DATA_DIR.mkdir(exist_ok=True)
CHARTS_DIR.mkdir(exist_ok=True)

# Load environment variables
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

# Admin user IDs (list of ints)
raw_admins = os.getenv("ADMIN_USER_IDS", "").strip()
ADMIN_IDS = set()
if raw_admins:
    for item in raw_admins.split(","):
        clean_item = item.strip()
        if clean_item.isdigit():
            ADMIN_IDS.add(int(clean_item))

DB_PATH = DATA_DIR / "weather_bot.db"

DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "bn")
DEFAULT_TEMP_UNIT = os.getenv("DEFAULT_TEMP_UNIT", "C")
DEFAULT_TIMEZONE = os.getenv("TIMEZONE", "Asia/Dhaka")

# Open-Meteo API Endpoints (100% Free, No API Key Required)
OPEN_METEO_GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
