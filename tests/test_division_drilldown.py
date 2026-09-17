import os
import sys
import asyncio

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.bd_geocoder import (
    get_all_divisions,
    get_districts_by_division,
    get_upazilas_by_district,
    find_bd_location
)
from handlers.division_handler import (
    build_divisions_keyboard,
    build_districts_keyboard,
    build_upazilas_keyboard,
    build_upazila_weather_buttons,
    build_lightning_divisions_keyboard,
    build_lightning_districts_keyboard,
    build_lightning_upazilas_keyboard,
    build_upazila_lightning_buttons,
    build_hourly_divisions_keyboard,
    build_hourly_districts_keyboard,
    build_hourly_upazilas_keyboard,
    build_upazila_hourly_buttons,
    build_daily_divisions_keyboard,
    build_daily_districts_keyboard,
    build_daily_upazilas_keyboard,
    build_upazila_daily_buttons
)
from handlers.common import get_main_keyboard
from services.weather_api import get_weather_data
from handlers.weather_handler import format_current_weather_card, format_lightning_alert_card
from handlers.forecast_handler import format_hourly_message, format_daily_forecast_message

async def run_tests():
    print("========================================")
    print("🧪 Testing Division -> District -> Upazila Navigation")
    print("========================================")

    # 1. Test 8 Divisions
    print("\n[1/6] Testing 8 Administrative Divisions...")
    divs = get_all_divisions()
    assert len(divs) == 8, f"Expected 8 divisions, got {len(divs)}"
    div_names = [d["bn"] for d in divs]
    print(f"  ✅ Found 8 divisions: {', '.join(div_names)}")

    # 2. Test 64 Districts across 8 Divisions
    print("\n[2/6] Testing 64 Districts across 8 Divisions...")
    total_districts = 0
    for d in divs:
        dists = get_districts_by_division(d["en"])
        total_districts += len(dists)
        print(f"  📍 {d['bn']} ({d['en']}): {len(dists)} districts")
    assert total_districts == 64, f"Expected 64 districts, got {total_districts}"
    print(f"  ✅ All {total_districts} districts correctly indexed!")

    # 3. Test Upazilas for Key Districts
    print("\n[3/6] Testing Upazilas per District...")
    test_cases = [
        ("Cumilla", 19, "বড়ুরা"),
        ("Kushtia", 6, "মিরপুর"),
        ("Sirajgonj", 9, "তারাশ"),
        ("Rangpur", 8, "তারাগঞ্জ"),
        ("Dhaka", 53, "মিরপুর")
    ]
    for dist_en, min_expected, sample_upz in test_cases:
        upzs = get_upazilas_by_district(dist_en)
        assert len(upzs) >= min_expected, f"Expected at least {min_expected} for {dist_en}, got {len(upzs)}"
        names = [u["name_bn"] for u in upzs]
        assert any(sample_upz in n for n in names), f"Sample {sample_upz} not found in {names}"
        print(f"  📍 {dist_en}: {len(upzs)} upazilas (sample: {sample_upz} verified)")
    print("  ✅ Upazilas verification passed!")

    # 4. Test Inline Keyboard Generation & Telegram 64-Byte Callback Limit
    print("\n[4/6] Testing Inline Keyboards & Callback Size...")
    # Division Keyboard
    div_kb = build_divisions_keyboard()
    for row in div_kb.inline_keyboard:
        for btn in row:
            assert len(btn.callback_data.encode('utf-8')) <= 64, f"Callback too long: {btn.callback_data}"
    print(f"  ✅ Division keyboard: {sum(len(r) for r in div_kb.inline_keyboard)} buttons valid")

    # District Keyboard (Dhaka)
    dist_kb = build_districts_keyboard("Dhaka")
    for row in dist_kb.inline_keyboard:
        for btn in row:
            assert len(btn.callback_data.encode('utf-8')) <= 64, f"Callback too long: {btn.callback_data}"
    print(f"  ✅ District keyboard (Dhaka): {sum(len(r) for r in dist_kb.inline_keyboard)} buttons valid")

    # Upazila Keyboard (Cumilla - 19 upazilas, paginated)
    upz_kb_p0 = build_upazilas_keyboard("Cumilla", page=0)
    for row in upz_kb_p0.inline_keyboard:
        for btn in row:
            assert len(btn.callback_data.encode('utf-8')) <= 64, f"Callback too long: {btn.callback_data}"
    print(f"  ✅ Upazila keyboard (Cumilla P0): {sum(len(r) for r in upz_kb_p0.inline_keyboard)} buttons valid")

    upz_kb_p1 = build_upazilas_keyboard("Cumilla", page=1)
    for row in upz_kb_p1.inline_keyboard:
        for btn in row:
            assert len(btn.callback_data.encode('utf-8')) <= 64, f"Callback too long: {btn.callback_data}"
    print(f"  ✅ Upazila keyboard (Cumilla P1): {sum(len(r) for r in upz_kb_p1.inline_keyboard)} buttons valid")

    # 5. Test Live Weather Card for an Upazila (Barura)
    print("\n[5/6] Testing Live Weather Card for Barura (বড়ুরা, কুমিল্লা)...")
    barura = find_bd_location("Barura")
    assert barura is not None
    w = await get_weather_data(barura["lat"], barura["lon"], "C")
    assert w is not None
    card = format_current_weather_card(w, barura["display_name"], "bn", "C")
    assert "বড়ুরা" in card or "Barura" in card
    assert "তাপমাত্রা" in card
    print("  ✅ Real-time weather card generated successfully for Barura!")

    # 6. Test Streamlined Reply Keyboard
    print("\n[6/6] Testing Streamlined 4-Button Reply Keyboard (Division, Lightning, 24h, 7-day)...")
    rk = get_main_keyboard("bn")
    button_rows = [[btn.text if hasattr(btn, 'text') else str(btn) for btn in row] for row in rk.keyboard]
    print(f"  🔘 Main Keyboard layout: {button_rows}")
    assert len(button_rows) == 2, f"Expected 2 rows, got {len(button_rows)}"
    assert button_rows[0] == ["🏢 বিভাগ", "⚡ বজ্রপাত সতর্কতা"]
    assert button_rows[1] == ["📆 ২৪ ঘণ্টার পূর্বাভাস", "📅 ৭ দিনের পূর্বাভাস"]
    total_buttons = sum(len(r) for r in button_rows)
    assert total_buttons == 4, f"Expected 4 buttons, got {total_buttons}"
    print("  ✅ Reply Keyboard strictly matches user's request (exactly 4 buttons: Division, Lightning, 24h, 7-Day)!")

    # 7. Test Dedicated Lightning Alert Drilldown Keyboards & Cards
    print("\n[7/7] Testing Dedicated Lightning Alert Keyboards & Localized Card...")
    # Lightning Division Keyboard
    ldiv_kb = build_lightning_divisions_keyboard()
    ldiv_buttons = [btn for row in ldiv_kb.inline_keyboard for btn in row]
    assert len(ldiv_buttons) == 8, f"Expected 8 division buttons, got {len(ldiv_buttons)}"
    for btn in ldiv_buttons:
        assert btn.callback_data.startswith("ldiv:"), f"Invalid prefix: {btn.callback_data}"
        assert len(btn.callback_data.encode('utf-8')) <= 64
    print("  ✅ Lightning 8-division keyboard verified!")

    # Lightning District Keyboard (Chattogram)
    ldist_kb = build_lightning_districts_keyboard("Chattogram")
    ldist_buttons = [btn for row in ldist_kb.inline_keyboard for btn in row]
    assert any(b.callback_data == "ldist:Cumilla" for b in ldist_buttons)
    assert any(b.callback_data == "lback:div" for b in ldist_buttons)
    for btn in ldist_buttons:
        assert len(btn.callback_data.encode('utf-8')) <= 64
    print("  ✅ Lightning district keyboard (Chattogram) verified with Cumilla & lback:div!")

    # Lightning Upazila Keyboard (Cumilla)
    lupz_kb = build_lightning_upazilas_keyboard("Cumilla", page=0)
    lupz_buttons = [btn for row in lupz_kb.inline_keyboard for btn in row]
    assert any("কুমিল্লা সদর" in b.text for b in lupz_buttons)
    assert any(b.callback_data.startswith("ldist_p:") for b in lupz_buttons)  # pagination
    assert any(b.callback_data.startswith("lback:dist:") for b in lupz_buttons)  # back to dist
    for btn in lupz_buttons:
        if btn.callback_data != "noop":
            assert len(btn.callback_data.encode('utf-8')) <= 64
    print("  ✅ Lightning upazila keyboard (Cumilla) verified with pagination & back button!")

    # Upazila Lightning Action Buttons
    l_act_kb = build_upazila_lightning_buttons(barura["lat"], barura["lon"], barura["name"], "Cumilla", "bn")
    act_buttons = [btn for row in l_act_kb.inline_keyboard for btn in row]
    assert any(b.callback_data.startswith("lref:") for b in act_buttons)
    assert any(b.callback_data == "lback:upz:Cumilla" for b in act_buttons)
    assert any(b.callback_data.startswith("hr:") for b in act_buttons)
    assert any(b.callback_data.startswith("ref:") for b in act_buttons)
    print("  ✅ Upazila lightning action buttons (lref, lback:upz, hr, ref) verified!")

    # Localized Lightning Alert Card
    l_card = format_lightning_alert_card(w, barura["display_name"], "bn", "C")
    assert "বজ্রপাত" in l_card
    assert "ঝুঁকির মাত্রা" in l_card
    assert "জরুরি জীবনরক্ষাকারী সতর্কতা" in l_card
    print("  ✅ Dedicated localized Lightning Alert Card verified for Barura, Cumilla!")

    # 8. Test 24-Hour Forecast (Hourly) Drilldown Keyboards & Cards
    print("\n[8/9] Testing 24-Hour Forecast (Hourly) Keyboards & Localized Card...")
    # Hourly Division Keyboard
    hdiv_kb = build_hourly_divisions_keyboard()
    hdiv_buttons = [btn for row in hdiv_kb.inline_keyboard for btn in row]
    assert len(hdiv_buttons) == 8, f"Expected 8 division buttons, got {len(hdiv_buttons)}"
    for btn in hdiv_buttons:
        assert btn.callback_data.startswith("hdiv:"), f"Invalid prefix: {btn.callback_data}"
        assert len(btn.callback_data.encode('utf-8')) <= 64
    print("  ✅ Hourly 8-division keyboard verified!")

    # Hourly District Keyboard (Chattogram)
    hdist_kb = build_hourly_districts_keyboard("Chattogram")
    hdist_buttons = [btn for row in hdist_kb.inline_keyboard for btn in row]
    assert any(b.callback_data == "hdist:Cumilla" for b in hdist_buttons)
    assert any(b.callback_data == "hback:div" for b in hdist_buttons)
    for btn in hdist_buttons:
        assert len(btn.callback_data.encode('utf-8')) <= 64
    print("  ✅ Hourly district keyboard (Chattogram) verified with Cumilla & hback:div!")

    # Hourly Upazila Keyboard (Cumilla)
    hupz_kb = build_hourly_upazilas_keyboard("Cumilla", page=0)
    hupz_buttons = [btn for row in hupz_kb.inline_keyboard for btn in row]
    assert any("কুমিল্লা সদর" in b.text for b in hupz_buttons)
    assert any(b.callback_data.startswith("hdist_p:") for b in hupz_buttons)
    assert any(b.callback_data.startswith("hback:dist:") for b in hupz_buttons)
    for btn in hupz_buttons:
        if btn.callback_data != "noop":
            assert len(btn.callback_data.encode('utf-8')) <= 64
    print("  ✅ Hourly upazila keyboard (Cumilla) verified with pagination & back button!")

    # Hourly Action Buttons
    h_act_kb = build_upazila_hourly_buttons(barura["lat"], barura["lon"], barura["name"], "Cumilla", "bn")
    h_buttons = [btn for row in h_act_kb.inline_keyboard for btn in row]
    assert any(b.callback_data.startswith("href:") for b in h_buttons)
    assert any(b.callback_data == "hback:upz:Cumilla" for b in h_buttons)
    assert any(b.callback_data.startswith("fc:") for b in h_buttons)
    assert any(b.callback_data.startswith("lref:") for b in h_buttons)
    print("  ✅ Hourly action buttons (href, hback:upz, fc, lref) verified!")

    # Localized 24-Hour Forecast Card
    h_card = format_hourly_message(w, barura["display_name"], "bn", "C")
    assert "২৪ ঘণ্টার" in h_card
    assert "পূর্বাভাস" in h_card
    print("  ✅ Dedicated localized 24-Hour Forecast Card verified for Barura, Cumilla!")

    # 9. Test 7-Day Forecast (Daily) Drilldown Keyboards & Cards
    print("\n[9/9] Testing 7-Day Forecast (Daily) Keyboards & Localized Card...")
    # Daily Division Keyboard
    ddiv_kb = build_daily_divisions_keyboard()
    ddiv_buttons = [btn for row in ddiv_kb.inline_keyboard for btn in row]
    assert len(ddiv_buttons) == 8, f"Expected 8 division buttons, got {len(ddiv_buttons)}"
    for btn in ddiv_buttons:
        assert btn.callback_data.startswith("ddiv:"), f"Invalid prefix: {btn.callback_data}"
        assert len(btn.callback_data.encode('utf-8')) <= 64
    print("  ✅ Daily 8-division keyboard verified!")

    # Daily District Keyboard (Chattogram)
    ddist_kb = build_daily_districts_keyboard("Chattogram")
    ddist_buttons = [btn for row in ddist_kb.inline_keyboard for btn in row]
    assert any(b.callback_data == "ddist:Cumilla" for b in ddist_buttons)
    assert any(b.callback_data == "dback:div" for b in ddist_buttons)
    for btn in ddist_buttons:
        assert len(btn.callback_data.encode('utf-8')) <= 64
    print("  ✅ Daily district keyboard (Chattogram) verified with Cumilla & dback:div!")

    # Daily Upazila Keyboard (Cumilla)
    dupz_kb = build_daily_upazilas_keyboard("Cumilla", page=0)
    dupz_buttons = [btn for row in dupz_kb.inline_keyboard for btn in row]
    assert any("কুমিল্লা সদর" in b.text for b in dupz_buttons)
    assert any(b.callback_data.startswith("ddist_p:") for b in dupz_buttons)
    assert any(b.callback_data.startswith("dback:dist:") for b in dupz_buttons)
    for btn in dupz_buttons:
        if btn.callback_data != "noop":
            assert len(btn.callback_data.encode('utf-8')) <= 64
    print("  ✅ Daily upazila keyboard (Cumilla) verified with pagination & back button!")

    # Daily Action Buttons
    d_act_kb = build_upazila_daily_buttons(barura["lat"], barura["lon"], barura["name"], "Cumilla", "bn")
    d_buttons = [btn for row in d_act_kb.inline_keyboard for btn in row]
    assert any(b.callback_data.startswith("dref:") for b in d_buttons)
    assert any(b.callback_data == "dback:upz:Cumilla" for b in d_buttons)
    assert any(b.callback_data.startswith("hr:") for b in d_buttons)
    assert any(b.callback_data.startswith("lref:") for b in d_buttons)
    print("  ✅ Daily action buttons (dref, dback:upz, hr, lref) verified!")

    # Localized 7-Day Forecast Card
    d_card = format_daily_forecast_message(w, barura["display_name"], "bn", "C")
    assert "৭ দিনের" in d_card
    assert "পূর্বাভাস" in d_card
    print("  ✅ Dedicated localized 7-Day Forecast Card verified for Barura, Cumilla!")

    print("\n========================================")
    print("🎉 ALL 4 MAIN BUTTON DRILLDOWN TESTS PASSED! (100% SUCCESS)")
    print("========================================")

if __name__ == "__main__":
    asyncio.run(run_tests())