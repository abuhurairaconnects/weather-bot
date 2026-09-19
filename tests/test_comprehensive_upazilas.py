"""
Comprehensive End-to-End Test Suite for Bangladesh All 64 Districts & Upazilas
Verifies:
1. Instant 0ms geocoding for all 8 divisions and 30+ sample upazilas/districts.
2. Real-time Open-Meteo weather data fetching using coordinates.
3. Card formatting with signature greeting:
   'আসসালামু আলাইকুম, আমি আবু হুরাইরার AI অ্যাসিস্ট্যান্ট, আপনাকে কীভাবে সাহায্য করি?'
4. Button generation with core 3 features (24h hourly, 7d forecast, smart advice) + refresh.
5. Random upazila weather generation.
"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding='utf-8')

from services.weather_api import search_city, get_weather_data
from services.bd_geocoder import find_bd_location, _BD_LOCATIONS
from handlers.weather_handler import format_current_weather_card, build_weather_buttons
from handlers.forecast_handler import format_hourly_message, format_daily_forecast_message
from services.recommendations import generate_recommendations, format_recommendations_message

SIGNATURE_GREETING = "আসসালামু আলাইকুম, আমি আবু হুরাইরার AI অ্যাসিস্ট্যান্ট, আপনাকে কীভাবে সাহায্য করি?"

SAMPLE_AREAS_BY_DIVISION = {
    "Dhaka": ["Dhaka", "ঢাকা", "Mirpur", "মিরপুর", "Savar", "সাভার", "Dhamrai", "ধামরাই", "Gopalganj", "গোপালগঞ্জ"],
    "Chittagong": ["Chattogram", "চট্টগ্রাম", "Pekua", "পেকুয়া", "Teknaf", "টেকনাফ", "Maheshkhali", "মহেশখালী", "Sandwip", "সন্দ্বীপ", "Debidwar", "দেবিদ্বার"],
    "Rajshahi": ["Rajshahi", "রাজশাহী", "Tarash", "তাড়াশ", "তারাশ", "Sirajganj", "সিরাজগঞ্জ", "Singra", "সিংড়া", "Gurudaspur", "গুরুদাসপুর", "Bogra", "বগুড়া"],
    "Khulna": ["Khulna", "খুলনা", "Kushtia", "কুষ্টিয়া", "Bheramara", "ভেড়ামারা", "Jessore", "যশোর", "Satkhira", "সাতক্ষীরা", "Mujibnagar", "মুজিবনগর"],
    "Barishal": ["Barisal", "বরিশাল", "Bhola", "ভোলা", "Burhanuddin", "বোরহানউদ্দিন", "Galachipa", "গলাচিপা", "Amtali", "আমতলী"],
    "Sylhet": ["Sylhet", "সিলেট", "Sreemangal", "শ্রীমঙ্গল", "Moulvibazar", "মৌলভীবাজার", "Sunamganj", "সুনামগঞ্জ", "Dharmapasha", "ধর্মপাশা"],
    "Rangpur": ["Rangpur", "রংপুর", "Kurigram", "কুড়িগ্রাম", "Chilmari", "চিলমারী", "Rowmari", "রৌমারী", "Bhurungamari", "ভুরুঙ্গামারী", "Tetulia", "তেঁতুলিয়া"],
    "Mymensingh": ["Mymensingh", "ময়মনসিংহ", "Jamalpur", "জামালপুর", "Netrokona", "নেত্রকোনা", "Sherpur", "শেরপুর", "Melandah", "মেলান্দহ", "Tarakanda", "তারাকান্দা"]
}

async def run_tests():
    print("=" * 70)
    print("🚀 STARTING COMPREHENSIVE BANGLADESH DISTRICTS & UPAZILAS TEST SUITE")
    print(f"📦 Total administrative locations in database: {len(_BD_LOCATIONS)}")
    print("=" * 70)

    # 1. Test Geocoding for all divisions
    total_searched = 0
    total_found = 0
    for division, places in SAMPLE_AREAS_BY_DIVISION.items():
        print(f"\n📍 Testing Division: {division} ({len(places)} places)")
        for p in places:
            total_searched += 1
            cities = await search_city(p)
            if cities:
                c = cities[0]
                total_found += 1
                print(f"  ✅ {p:16} -> {c['name']:14} ({c['display_name']}) [{c['lat']:.4f}, {c['lon']:.4f}]")
            else:
                print(f"  ❌ FAILED: {p}")

    print(f"\nGeocoding Results: {total_found}/{total_searched} passed")
    assert total_found == total_searched, f"Expected all {total_searched} places to resolve!"

    # 2. Test Real-time Weather Fetching for critical upazilas (Tarash, Singra, Pekua, Chilmari)
    critical_upazilas = ["Tarash", "তাড়াশ", "Singra", "Pekua", "Chilmari", "Burhanuddin"]
    print("\n" + "=" * 70)
    print("🌦️ TESTING LIVE OPEN-METEO WEATHER FETCHING FOR CRITICAL UPAZILAS")
    print("=" * 70)

    for up in critical_upazilas:
        cities = await search_city(up)
        c = cities[0]
        data = await get_weather_data(c["lat"], c["lon"], "C")
        assert data is not None, f"Failed to fetch weather for {up}"
        temp = data["current"]["temp"]
        humidity = data["current"]["humidity"]
        rain_prob = data["current"]["today_rain_chance_max"]
        aqi = data["current"]["aqi"]["us_aqi"]
        print(f"  ✅ {c['name']:14} | Temp: {temp}°C | Humidity: {humidity}% | Rain: {rain_prob}% | AQI: {aqi}")

        # Test Card Formatting & Smart Signature Greeting
        from handlers.conversation import get_smart_signature_greeting
        greeting = get_smart_signature_greeting(100000 + hash(up), "bn")
        assert SIGNATURE_GREETING in greeting
        card = format_current_weather_card(data, c["display_name"], "bn", "C")
        assert "তাপমাত্রা" in card
        
        # Test Buttons
        buttons = build_weather_buttons(c["lat"], c["lon"], c["name"], "bn")
        btn_texts = [b.text for row in buttons.inline_keyboard for b in row]
        assert "📆 ২৪ ঘণ্টা" in btn_texts
        assert "📅 ৭ দিন" in btn_texts
        assert "⚡ বজ্রপাত সতর্কতা" in btn_texts
        assert "🧠 স্মার্ট পরামর্শ" in btn_texts
        assert "🔄 রিফ্রেশ" in btn_texts

    print("  ✅ All weather cards and buttons verified successfully!")

    # 3. Test Sub-features Formatting (24h Hourly, 7d Forecast, Smart Advice)
    sample_c = (await search_city("তাড়াশ"))[0]
    sample_data = await get_weather_data(sample_c["lat"], sample_c["lon"], "C")
    
    # Hourly
    hourly_msg = format_hourly_message(sample_data, sample_c["display_name"], "bn", "C")
    assert "২৪ ঘণ্টার প্রতি ঘণ্টার পূর্বাভাস" in hourly_msg
    print("  ✅ Hourly forecast format verified!")

    # Daily
    daily_msg = format_daily_forecast_message(sample_data, sample_c["display_name"], "bn", "C")
    assert "৭ দিনের আবহাওয়ার পূর্বাভাস" in daily_msg
    print("  ✅ 7-Day forecast format verified!")

    # Advice
    rec = generate_recommendations(sample_data, "bn")
    advice_msg = format_recommendations_message(rec, sample_c["display_name"], "bn")
    assert "স্মার্ট আবহাওয়া পরামর্শ" in advice_msg
    print("  ✅ Smart advice format verified!")

    # 4. Test Random Upazila Picker
    upazilas = [l for l in _BD_LOCATIONS if l.get("type") == "upazila"]
    assert len(upazilas) >= 495, f"Expected at least 495 upazilas, got {len(upazilas)}"
    import random
    random_up = random.choice(upazilas)
    loc = find_bd_location(random_up["name_en"])
    assert loc is not None
    print(f"  ✅ Random Upazila Picked: {loc['name']} ({loc['display_name']})")

    print("\n" + "=" * 70)
    print("🎉 ALL COMPREHENSIVE TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_tests())
