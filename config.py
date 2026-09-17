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

# Primary Developer & Admin ID
PRIMARY_ADMIN_ID = 8953572486

# Admin user IDs (list of ints)
raw_admins = os.getenv("ADMIN_USER_IDS", "").strip()
ADMIN_IDS = {PRIMARY_ADMIN_ID}
if raw_admins:
    for item in raw_admins.split(","):
        clean_item = item.strip()
        if clean_item.isdigit():
            ADMIN_IDS.add(int(clean_item))

# Strict Admin-Only Access Mode (False: allow all public users to get weather info)
ONLY_ADMIN_ACCESS = os.getenv("ONLY_ADMIN_ACCESS", "false").lower() in ("true", "1", "yes")

def is_admin(user_id: int) -> bool:
    """Check if the given user is the primary developer / administrator."""
    return bool(user_id and user_id in ADMIN_IDS)

def is_authorized(user_id: int) -> bool:
    """Check if user can access weather features. Public access enabled so everyone can use it."""
    if ONLY_ADMIN_ACCESS:
        return is_admin(user_id)
    return True

ACCESS_DENIED_MESSAGE_BN = (
    "⛔ **অ্যাক্সেস সীমাবদ্ধ (Access Denied)**\n\n"
    "দুঃখিত! এটি **আবু হুরাইরার** ব্যক্তিগত (Private) AI অ্যাসিস্ট্যান্ট বট। "
    "শুধুমাত্র অনুমোদিত অ্যাডমিন ছাড়া অন্য কারো এটি ব্যবহারের অনুমতি নেই।"
)

ACCESS_DENIED_MESSAGE_EN = (
    "⛔ **Access Denied**\n\n"
    "Sorry! This is a private AI assistant bot for **Abu Huraira**. "
    "Only authorized administrators can access this bot."
)

DB_PATH = DATA_DIR / "weather_bot.db"

DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "bn")
DEFAULT_TEMP_UNIT = os.getenv("DEFAULT_TEMP_UNIT", "C")
DEFAULT_TIMEZONE = os.getenv("TIMEZONE", "Asia/Dhaka")

# Open-Meteo API Endpoints (100% Free, No API Key Required)
OPEN_METEO_GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

# Google Gemini AI Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
GEMINI_MODELS = ["gemini-flash-lite-latest", "gemini-flash-latest"]
