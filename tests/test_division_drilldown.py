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
    build_upazila_weather_buttons
)
from handlers.common import get_main_keyboard
from services.weather_api import get_weather_data
from handlers.weather_handler import format_current_weather_card

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

    print("\n========================================")
    print("🎉 ALL DIVISION DRILLDOWN TESTS PASSED! (100% SUCCESS)")
    print("========================================")

if __name__ == "__main__":
    asyncio.run(run_tests())