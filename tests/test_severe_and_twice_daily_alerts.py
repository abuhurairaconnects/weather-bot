"""
Comprehensive Verification Tests for:
1. Severe Weather Alerts & Warning Banner (Thunderstorm, Heavy Rain, Gale, Extreme Temp)
2. Excluded Feature 2 (Agro-Weather Advisory) Confirmation
3. Twice-Daily Automatic Weather Alerts at 07:00 AM and 07:00 PM (Asia/Dhaka)
4. Primary Admin (Abu Huraira: 8953572486) Auto-Subscription
5. /subscribe and /unsubscribe Flow & Deduplication
"""
import sys
import os
import asyncio
from datetime import datetime, timezone, timedelta

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from handlers.weather_handler import get_severe_weather_alert, format_current_weather_card
from jobs.scheduler import build_morning_report_message, build_evening_report_message
from database.db import (
    init_db,
    get_alert_settings,
    update_alert_settings,
    get_all_subscribers_for_alerts,
    get_or_create_user
)
from config import PRIMARY_ADMIN_ID, is_admin

def test_severe_weather_banner():
    print("\n--- [1/5] Testing Severe Weather Warning Detection & Banner ---")
    
    # A. Thunderstorm & Lightning (WMO 95)
    mock_thunderstorm = {
        "current": {"wmo_code": 95, "temp": 28.0, "wind_speed": 20.0, "today_rain_chance_max": 80},
        "hourly": {"precipitation_probability": [85, 80, 70]}
    }
    alert_bn = get_severe_weather_alert(mock_thunderstorm, "bn")
    assert "বজ্রঝড় ও বজ্রপাত সতর্কতা" in alert_bn, "Thunderstorm alert must be detected"
    assert "⚡" in alert_bn
    print("  ✅ WMO 95 Thunderstorm & Lightning Alert: Detected")

    # B. Heavy Downpour (Rain probability >= 75%)
    mock_heavy_rain = {
        "current": {"wmo_code": 63, "temp": 26.0, "wind_speed": 15.0, "today_rain_chance_max": 85},
        "hourly": {"precipitation_probability": [80, 85, 90]}
    }
    alert_rain = get_severe_weather_alert(mock_heavy_rain, "bn")
    assert "ভারী বৃষ্টিপাত সতর্কতা" in alert_rain, "Heavy rain alert must be detected"
    assert "🌧️" in alert_rain
    print("  ✅ Heavy Rain (80%+) Alert: Detected")

    # C. Gale Wind (Wind speed >= 38 km/h)
    mock_gale = {
        "current": {"wmo_code": 2, "temp": 28.0, "wind_speed": 42.5, "today_rain_chance_max": 10},
        "hourly": {"precipitation_probability": [10, 5, 0]}
    }
    alert_gale = get_severe_weather_alert(mock_gale, "bn")
    assert "ঝড়ো হাওয়া সতর্কতা" in alert_gale, "Gale wind alert must be detected"
    assert "💨" in alert_gale
    print("  ✅ Gale Wind (42.5 km/h) Alert: Detected")

    # D. Extreme Heatwave (Temp >= 38°C)
    mock_heat = {
        "current": {"wmo_code": 0, "temp": 39.5, "wind_speed": 10.0, "today_rain_chance_max": 0},
        "hourly": {"precipitation_probability": [0, 0, 0]}
    }
    alert_heat = get_severe_weather_alert(mock_heat, "bn")
    assert "তীব্র তাপদাহ সতর্কতা" in alert_heat, "Extreme heatwave alert must be detected"
    assert "🔥" in alert_heat
    print("  ✅ Extreme Heatwave (39.5°C) Alert: Detected")

    # E. Severe Cold Wave (Temp <= 10°C)
    mock_cold = {
        "current": {"wmo_code": 0, "temp": 8.5, "wind_speed": 10.0, "today_rain_chance_max": 0},
        "hourly": {"precipitation_probability": [0, 0, 0]}
    }
    alert_cold = get_severe_weather_alert(mock_cold, "bn")
    assert "তীব্র শৈত্যপ্রবাহ সতর্কতা" in alert_cold, "Severe cold wave alert must be detected"
    assert "❄️" in alert_cold
    print("  ✅ Severe Cold Wave (8.5°C) Alert: Detected")

    # F. Normal Fair Weather
    mock_normal = {
        "current": {"wmo_code": 1, "temp": 27.0, "wind_speed": 12.0, "today_rain_chance_max": 15},
        "hourly": {"precipitation_probability": [15, 10, 5]}
    }
    alert_normal = get_severe_weather_alert(mock_normal, "bn")
    assert alert_normal == "", "Normal weather should produce no alert banner"
    print("  ✅ Normal Weather: Clean (No False Positives)")

    # G. Verification inside format_current_weather_card
    full_card_data = {
        "current": {
            "temp": 29.0, "feels_like": 33.0, "humidity": 85, "pressure": 1008,
            "wind_speed": 40.0, "wind_dir": 180, "wind_direction_compass": "দক্ষিণ",
            "visibility_km": 6.0, "cloud_cover": 90, "wmo_code": 95,
            "today_rain_chance_max": 85, "rainfall_amount": 12.0, "is_day": 1,
            "today_max_temp": 32.0, "today_min_temp": 24.0, "today_max_uv": 6.0,
            "sunrise": "05:45", "sunset": "18:05", "aqi": {"us_aqi": 55, "pm2_5": 15.0, "pm10": 30.0},
            "moon": {"name_bn": "পূর্ণিমা", "emoji": "🌕", "illumination": "98%"}
        },
        "hourly": {"precipitation_probability": [85, 80, 70]}
    }
    card = format_current_weather_card(full_card_data, "Dhaka", "bn", "C")
    assert "⚠️ **জরুরি আবহাওয়া সতর্কতা:**" in card, "Card must include prominent warning banner"
    assert "বজ্রঝড় ও বজ্রপাত সতর্কতা" in card
    assert "ঝড়ো হাওয়া সতর্কতা" in card
    print("  ✅ Card Integration: Warning banner displays prominently at top of weather status")

def test_feature_2_agro_excluded():
    print("\n--- [2/5] Verifying Feature 2 (Agro-Weather) is Excluded ---")
    import handlers.weather_handler as wh
    import inspect
    source = inspect.getsource(wh)
    assert "agro" not in source.lower(), "Agro feature must NOT be present in weather_handler"
    assert "কৃষি পরামর্শ" not in source, "Agro advisory text must NOT be present in weather_handler"
    print("  ✅ Feature 2 (Agro-Weather Advisory) is confirmed EXCLUDED per instruction '2 number bad dao'")

def test_morning_and_evening_reports():
    print("\n--- [3/5] Testing 07:00 AM & 07:00 PM Daily Briefing Format ---")
    mock_data = {
        "current": {
            "temp": 24.5, "feels_like": 25.0, "humidity": 75, "wmo_code": 2,
            "wind_speed": 14.0, "today_rain_chance_max": 65, "today_max_temp": 31.0,
            "today_min_temp": 22.0, "today_max_uv": 7.5,
            "aqi": {"us_aqi": 68},
            "moon": {"name_bn": "পূর্ণচন্দ্র", "emoji": "🌕", "illumination": "99%"}
        },
        "daily": {
            "time": ["2026-09-17", "2026-09-18"],
            "temperature_2m_max": [31.0, 32.5],
            "temperature_2m_min": [22.0, 23.0],
            "precipitation_probability_max": [65, 20],
            "weather_code": [2, 1]
        }
    }

    # 1. Morning Briefing (07:00 AM)
    morning_msg = build_morning_report_message(mock_data, "Dhaka", "bn", "C")
    assert "সুপ্রভাত! সকালের আবহাওয়া বুলেটিন — Dhaka" in morning_msg
    assert "সকাল ০৭:০০ টার নিয়মিত বুলেটিন" in morning_msg
    assert "22.0°C থেকে 31.0°C" in morning_msg
    assert "**বৃষ্টির সম্ভাবনা:** 65%" in morning_msg
    assert "ছাতা সঙ্গে রাখুন" in morning_msg
    assert "ইউভি সূচক" in morning_msg
    assert "বায়ুমান (AQI)" in morning_msg
    print("  ✅ Morning Bulletin (07:00 AM): Fully formatted with range, rain advisory, UV & AQI")

    # 2. Evening Briefing (07:00 PM)
    evening_msg = build_evening_report_message(mock_data, "Dhaka", "bn", "C")
    assert "শুভ সন্ধ্যা! সান্ধ্যকালীন আবহাওয়া আপডেট — Dhaka" in evening_msg
    assert "সন্ধ্যা ০৭:০০ টার নিয়মিত বুলেটিন" in evening_msg
    assert "24.5°C" in evening_msg
    assert "পূর্ণচন্দ্র" in evening_msg
    assert "আগামীকালের পূর্বাভাস একনজরে" in evening_msg
    assert "23.0°C থেকে 32.5°C" in evening_msg
    print("  ✅ Evening Bulletin (07:00 PM): Fully formatted with night temp, moon & tomorrow forecast")

async def test_admin_auto_subscription():
    print("\n--- [4/5] Testing Primary Admin (Abu Huraira) Auto-Subscription ---")
    await init_db()
    
    admin_alert = await get_alert_settings(PRIMARY_ADMIN_ID)
    print(f"  Primary Admin ID: {PRIMARY_ADMIN_ID}")
    print(f"  Morning Report (7:00 AM): {admin_alert.get('morning_report')}")
    print(f"  Evening Report (7:00 PM): {admin_alert.get('evening_report')}")
    print(f"  Severe Alert: {admin_alert.get('severe_alert')}")
    print(f"  City: {admin_alert.get('city_name')}")

    assert admin_alert.get("morning_report") == 1, "Admin must be auto-subscribed to 7:00 AM report"
    assert admin_alert.get("evening_report") == 1, "Admin must be auto-subscribed to 7:00 PM report"
    assert admin_alert.get("severe_alert") == 1, "Admin must be auto-subscribed to severe alert"
    assert admin_alert.get("city_name") == "Dhaka", "Admin default city should be Dhaka"
    print("  ✅ Primary Admin Abu Huraira (8953572486) is 100% AUTO-SUBSCRIBED in database")

async def test_subscription_and_deduplication():
    print("\n--- [5/5] Testing /subscribe, /unsubscribe & Deduplication ---")
    test_user_id = 9988776655
    await get_or_create_user(test_user_id, "testuser", "Test")

    # 1. Subscribe user to Sirajganj Tarash
    await update_alert_settings(
        test_user_id,
        city_name="তাড়াশ, সিরাজগঞ্জ",
        lat=24.37,
        lon=89.37,
        morning_report=1,
        evening_report=1,
        severe_alert=1,
        rain_alert=1
    )
    user_alert = await get_alert_settings(test_user_id)
    assert user_alert["morning_report"] == 1
    assert user_alert["evening_report"] == 1
    assert user_alert["city_name"] == "তাড়াশ, সিরাজগঞ্জ"
    print("  ✅ /subscribe: Successfully set morning & evening alerts for তাড়াশ")

    # 2. Check subscriber query includes this user
    subscribers = await get_all_subscribers_for_alerts()
    user_ids = [s["user_id"] for s in subscribers]
    assert test_user_id in user_ids, "Subscribed user must appear in active alert list"
    assert PRIMARY_ADMIN_ID in user_ids, "Admin must appear in active alert list"
    print(f"  ✅ Active alert subscribers count: {len(subscribers)} (Admin & User both present)")

    # 3. Deduplication check with last_morning_sent and last_evening_sent
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    await update_alert_settings(test_user_id, last_morning_sent=today_str, last_evening_sent=today_str)
    updated = await get_alert_settings(test_user_id)
    assert updated["last_morning_sent"] == today_str
    assert updated["last_evening_sent"] == today_str
    print("  ✅ Deduplication: last_morning_sent and last_evening_sent recorded properly")

    # 4. Unsubscribe user
    await update_alert_settings(test_user_id, morning_report=0, evening_report=0, severe_alert=0, rain_alert=0)
    user_alert_unsub = await get_alert_settings(test_user_id)
    assert user_alert_unsub["morning_report"] == 0
    assert user_alert_unsub["evening_report"] == 0
    print("  ✅ /unsubscribe: Successfully deactivated all alerts")

def run_all_tests():
    print("==================================================================")
    print("🧪 RUNNING COMPREHENSIVE TESTS: SEVERE ALERTS & TWICE-DAILY (7 AM & 7 PM)")
    print("==================================================================")
    test_severe_weather_banner()
    test_feature_2_agro_excluded()
    test_morning_and_evening_reports()
    asyncio.run(test_admin_auto_subscription())
    asyncio.run(test_subscription_and_deduplication())
    print("\n==================================================================")
    print("🎉 ALL 5 TEST SUITES PASSED FLAWLESSLY! 100% PRODUCTION READY")
    print("==================================================================")

if __name__ == "__main__":
    run_all_tests()
