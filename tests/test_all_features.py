"""
Automated Test Suite for Streamlined Weather Assistant Bot
Verifies:
1. Database Layer
2. Real-Time Weather for Any District & Random Upazila
3. Next 24-Hour Hourly Forecast
4. Next 7-Day Extended Forecast
5. Smart Recommendations (Umbrella, Clothing, UV)
6. Weather Card & Button Generation
7. Conversational NLP & Area Query Recognition
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
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from database.db import init_db, get_or_create_user, log_search
from services.weather_api import search_city, get_weather_data
from services.recommendations import generate_recommendations, format_recommendations_message
from handlers.weather_handler import format_current_weather_card, build_weather_buttons
from handlers.forecast_handler import format_hourly_message, format_daily_forecast_message
from services.nlp_parser import classify_intent

async def run_tests():
    print("========================================")
    print("🧪 Running Streamlined Core Weather Bot Test Suite")
    print("========================================")

    # 1. Database Operations
    print("\n[1/7] Testing SQLite Database...")
    await init_db()
    test_user_id = 999888777
    user = await get_or_create_user(test_user_id, "testuser", "Test")
    assert user["user_id"] == test_user_id, "User creation failed"
    await log_search(test_user_id, "Dhaka")
    print("  ✅ Database layer PASSED.")

    # 2. District & Random Upazila Geolocation & Weather
    print("\n[2/7] Testing Real-Time District & Upazila Weather (Dhaka, Kushtia, Mirpur, Teknaf)...")
    test_locations = ["Dhaka", "Kushtia", "মিরপুর", "টেকনাফ"]
    for loc in test_locations:
        cities = await search_city(loc)
        assert len(cities) > 0, f"Failed to search {loc}"
        top = cities[0]
        w = await get_weather_data(top["lat"], top["lon"], "C")
        assert w is not None, f"Failed to fetch weather for {loc}"
        cur = w["current"]
        assert "temp" in cur and cur["temp"] is not None
        print(f"  📍 Found {loc} ➡️ {top['display_name']}: {cur['temp']}°C, Humidity: {cur['humidity']}%")
    print("  ✅ District & Upazila Real-Time Weather PASSED.")

    # 3. Next 24-Hour Hourly Forecast
    print("\n[3/7] Testing Next 24-Hour Forecast (২৪ ঘণ্টার পূর্বাভাস)...")
    c_dhaka = (await search_city("Dhaka"))[0]
    w_dhaka = await get_weather_data(c_dhaka["lat"], c_dhaka["lon"], "C")
    hourly_msg = format_hourly_message(w_dhaka, c_dhaka["display_name"], lang="bn", unit="C")
    assert "২৪ ঘণ্টার" in hourly_msg
    assert "বৃষ্টি" in hourly_msg
    print(f"  📆 24h Message Generated:\n" + "\n".join(hourly_msg.split("\n")[:5]) + "\n  ...")
    print("  ✅ 24-Hour Forecast PASSED.")

    # 4. Next 7-Day Daily Forecast
    print("\n[4/7] Testing Next 7-Day Forecast (৭ দিনের পূর্বাভাস)...")
    daily_msg = format_daily_forecast_message(w_dhaka, c_dhaka["display_name"], lang="bn", unit="C")
    assert "৭ দিনের" in daily_msg
    assert "তাপমাত্রা" in daily_msg
    print(f"  📅 7-Day Message Generated:\n" + "\n".join(daily_msg.split("\n")[:5]) + "\n  ...")
    print("  ✅ 7-Day Forecast PASSED.")

    # 5. Smart Recommendations
    print("\n[5/7] Testing Smart Advice (স্মার্ট পরামর্শ)...")
    rec_bn = generate_recommendations(w_dhaka, lang="bn")
    assert "umbrella" in rec_bn and "clothing" in rec_bn
    rec_msg = format_recommendations_message(rec_bn, c_dhaka["display_name"], lang="bn")
    assert "স্মার্ট আবহাওয়া পরামর্শ" in rec_msg
    print("  ☂️ Umbrella Advice:", rec_bn["umbrella"])
    print("  🧥 Clothing Advice:", rec_bn["clothing"])
    print("  ✅ Smart Advice PASSED.")

    # 6. Real-Time Weather Card & Buttons
    print("\n[6/7] Testing Weather Card & Streamlined Inline Buttons...")
    card = format_current_weather_card(w_dhaka, c_dhaka["display_name"], lang="bn", unit="C")
    assert "রিয়েল-টাইম আবহাওয়া" in card
    from handlers.conversation import get_smart_signature_greeting
    greeting = get_smart_signature_greeting(888777, "bn")
    assert "আবু হুরাইরার AI অ্যাসিস্ট্যান্ট" in greeting

    markup = build_weather_buttons(c_dhaka["lat"], c_dhaka["lon"], c_dhaka["name"], lang="bn")
    button_texts = [btn.text for row in markup.inline_keyboard for btn in row]
    print(f"  🔘 Inline Buttons: {button_texts}")
    assert any("২৪ ঘণ্টা" in b for b in button_texts)
    assert any("৭ দিন" in b for b in button_texts)
    assert any("স্মার্ট পরামর্শ" in b for b in button_texts)
    assert any("রিফ্রেশ" in b for b in button_texts)
    # Ensure removed buttons are NOT present
    assert not any("কৃষি" in b for b in button_texts), "Agriculture button should be removed"
    assert not any("গ্রাফ" in b for b in button_texts), "Graph button should be removed"
    assert not any("ফেভারিট" in b for b in button_texts), "Favorite button should be removed"
    print("  ✅ Weather Card & Streamlined Buttons PASSED.")

    # 7. Conversational NLP & Area Query Recognition
    print("\n[7/7] Testing Conversational NLP Intent Parser...")
    test_cases = [
        ("কুষ্টিয়ার রিয়েল-টাইম ওয়েদার কেমন?", "general_weather", "কুষ্টিয়া"),
        ("আজ কি বৃষ্টি হবে?", "rain", "Dhaka"),
        ("ছাতা লাগবে কি?", "umbrella", "Dhaka"),
        ("আজকের তাপমাত্রা কত?", "temp", "Dhaka"),
        ("মিরপুর", "general_weather", "মিরপুর")
    ]
    for text, expected_intent, expected_city in test_cases:
        res = classify_intent(text)
        print(f"  🗣️ \"{text}\" ➡️ Intent: {res['intent']} | City: {res.get('city')}")
        assert res["intent"] == expected_intent, f"Failed for '{text}': got {res['intent']}, expected {expected_intent}"

    print("  ✅ Conversational NLP PASSED.")

    print("\n" + "=" * 40)
    print("🎉 ALL CORE FEATURE TESTS PASSED! (100% SUCCESS)")
    print("========================================")

if __name__ == "__main__":
    asyncio.run(run_tests())
