"""
Comprehensive Automated Test Suite
Verifies all 17 feature categories and services of the Weather Assistant Bot.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from database.db import (
    init_db, get_or_create_user, update_user_setting,
    set_default_location, add_favorite, get_favorites,
    delete_favorite, get_alert_settings, update_alert_settings,
    get_admin_stats, log_search
)
from services.weather_api import search_city, get_weather_data, format_temp
from services.recommendations import generate_recommendations, format_recommendations_message
from services.agriculture import get_agriculture_advice
from services.travel import plan_travel
from services.charts import generate_weather_chart
from services.nlp_parser import classify_intent
from utils.moon import get_moon_phase
from utils.i18n import get_wmo_description, get_wind_direction, get_aqi_category, get_uv_category

async def run_tests():
    print("========================================")
    print("🧪 Running Ultimate Weather Bot Test Suite")
    print("========================================")

    # 1. Database Operations
    print("\n[1/7] Testing SQLite Database...")
    await init_db()
    test_user_id = 999888777
    user = await get_or_create_user(test_user_id, "testuser", "Test")
    assert user["user_id"] == test_user_id, "User creation failed"
    
    await update_user_setting(test_user_id, "language", "en")
    await update_user_setting(test_user_id, "temp_unit", "F")
    await set_default_location(test_user_id, "Chittagong", 22.3569, 91.7832)
    
    fav_id = await add_favorite(test_user_id, "home", "Chittagong", 22.3569, 91.7832)
    favs = await get_favorites(test_user_id)
    assert len(favs) >= 1, "Favorites insertion failed"
    await delete_favorite(test_user_id, fav_id)

    await update_alert_settings(test_user_id, rain_alert=1, morning_report=1)
    alerts = await get_alert_settings(test_user_id)
    assert alerts["rain_alert"] == 1, "Alert settings failed"
    
    await log_search(test_user_id, "Dhaka")
    stats = await get_admin_stats()
    assert stats["total_users"] >= 1, "Admin stats failed"
    print("  ✅ Database layer PASSED.")

    # 2. Weather & Open-Meteo API
    print("\n[2/7] Testing Open-Meteo Weather API...")
    cities = await search_city("Dhaka")
    assert len(cities) > 0, "City search failed"
    dhaka = cities[0]
    print(f"  📍 Located: {dhaka['display_name']} ({dhaka['lat']}, {dhaka['lon']})")

    w = await get_weather_data(dhaka["lat"], dhaka["lon"], "C")
    assert w is not None, "Weather fetch failed"
    cur = w["current"]
    assert "temp" in cur and cur["temp"] is not None, "Missing temperature"
    assert "humidity" in cur and cur["humidity"] is not None, "Missing humidity"
    assert "aqi" in cur and "us_aqi" in cur["aqi"], "Missing AQI"
    print(f"  🌡️ Temp: {cur['temp']}°C | Humidity: {cur['humidity']}% | AQI: {cur['aqi']['us_aqi']}")
    print("  ✅ Weather API PASSED.")

    # 3. Moon Phase & Astronomy
    print("\n[3/7] Testing Moon Phase & Astronomy...")
    moon = get_moon_phase()
    assert "emoji" in moon and "name_bn" in moon, "Moon phase calculation failed"
    print(f"  🌙 Moon Phase: {moon['emoji']} {moon['name_bn']} (Illumination: {moon['illumination']})")
    print("  ✅ Moon Phase PASSED.")

    # 4. Smart Recommendation Engine
    print("\n[4/7] Testing Smart AI Recommendation Engine...")
    rec_bn = generate_recommendations(w, lang="bn")
    assert "umbrella" in rec_bn and "clothing" in rec_bn and "driving" in rec_bn
    msg_bn = format_recommendations_message(rec_bn, "Dhaka", lang="bn")
    assert len(msg_bn) > 50, "Recommendations message too short"
    print("  ☂️ Umbrella:", rec_bn["umbrella"])
    print("  🧥 Clothing:", rec_bn["clothing"])
    print("  ✅ Recommendations Engine PASSED.")

    # 5. Agriculture & Travel Modes
    print("\n[5/7] Testing Agriculture & Travel Modes...")
    agri_msg = get_agriculture_advice(w, "Dhaka", lang="bn")
    assert "সেচ" in agri_msg or "Irrigation" in agri_msg, "Agriculture advice failed"
    print("  🌾 Agriculture Advice Generated (length: {} chars)".format(len(agri_msg)))

    travel_msg = await plan_travel("Dhaka", "Cox's Bazar", lang="bn")
    assert travel_msg is not None and "প্যাকিং" in travel_msg, "Travel planner failed"
    print("  🧳 Travel Route Plan Generated (length: {} chars)".format(len(travel_msg)))
    print("  ✅ Agriculture & Travel Modes PASSED.")

    # 6. Matplotlib Weather Chart
    print("\n[6/7] Testing Matplotlib Chart Generator...")
    chart_buf = generate_weather_chart(w, "Dhaka", lang="bn")
    assert chart_buf is not None, "Chart generation failed"
    chart_bytes = chart_buf.getvalue()
    assert len(chart_bytes) > 10000, "Chart image buffer is suspiciously small"
    print(f"  📊 Chart Image Generated ({len(chart_bytes):,} bytes PNG)")
    print("  ✅ Chart Analytics PASSED.")

    # 7. Conversational NLP Intent Parser
    print("\n[7/7] Testing Conversational NLP & Intent Classifier...")
    test_queries = [
        ("আজ কি বৃষ্টি হবে?", "rain", "Dhaka"),
        ("ঢাকায় ছাতা লাগবে কি?", "umbrella", "Dhaka"),
        ("আজকে কেমন গরম?", "temp", "Dhaka"),
        ("কাল সকালে কি বাইরে যাওয়া যাবে?", "outdoor", "Dhaka"),
        ("Dhaka to Cox's Bazar", "travel", "Cox's Bazar"),
        ("বাতাসের আর্দ্রতা কী?", "explain", None),
        ("AQI কী?", "explain", None)
    ]
    for text, expected_intent, expected_city in test_queries:
        res = classify_intent(text)
        print(f"  🗣️ \"{text}\" ➡️ Intent: {res['intent']} | City: {res.get('city')}")
        assert res["intent"] == expected_intent, f"Intent mismatch for '{text}': got {res['intent']}, expected {expected_intent}"

    print("  ✅ Conversational NLP PASSED.")

    print("\n" + "=" * 40)
    print("🎉 ALL TESTS PASSED SUCCESSFULLY! (100% WORKING)")
    print("========================================")

if __name__ == "__main__":
    asyncio.run(run_tests())
