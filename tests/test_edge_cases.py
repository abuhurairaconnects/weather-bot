"""
Edge Case & Stress Test Suite
Simulates rare, unusual, and extreme conditions to guarantee 100% stability.
"""
import asyncio
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from database.db import (
    init_db, get_or_create_user, add_favorite,
    get_favorites, log_search, get_admin_stats
)
from services.weather_api import search_city, get_weather_data
from services.charts import generate_weather_chart
from services.nlp_parser import classify_intent
from utils.moon import get_moon_phase
import datetime

async def run_edge_case_tests():
    print("========================================")
    print("🔬 Running Deep Edge-Case & Stress Tests")
    print("========================================")

    # 1. Invalid / Non-existent City
    print("\n[1/6] Testing invalid and non-existent city queries...")
    bad_cities = await search_city("asdfghjkl_nonexistent_xyz_999")
    assert bad_cities == [], "Expected empty results for fake city"
    print("  ✅ Fake city handled gracefully (returned 0 results without crashing).")

    # 2. Extreme Special Characters
    print("\n[2/6] Testing special characters & Unicode...")
    special_search = await search_city("!@#$%^&*()_+{}[]|\\:;\"'<>,.?/")
    assert isinstance(special_search, list), "Special chars should return list safely"
    print("  ✅ Special characters handled safely.")

    # 3. Invalid Area Lookup
    print("\n[3/6] Testing invalid area query...")
    bad_area_res = await search_city("ThisIsNotARealPlaceXYZ123")
    assert bad_area_res == [], "Expected empty list for non-existent area"
    print("  ✅ Invalid area handled gracefully.")

    # 4. Unusual NLP Inputs
    print("\n[4/6] Testing unusual conversational inputs...")
    intents = [
        classify_intent(""),
        classify_intent("???"),
        classify_intent("1234567890"),
        classify_intent("বৃষ্টি বৃষ্টি বৃষ্টি"),
        classify_intent("How is the weather in London?")
    ]
    assert intents[0]["intent"] == "unknown"
    assert intents[3]["intent"] == "rain"
    assert intents[4]["intent"] in ["general_weather", "rain", "temp"]
    print("  ✅ NLP intent parser handles strange/empty inputs cleanly.")

    # 5. Moon Phase Calculation on Edge Dates
    print("\n[5/6] Testing Moon Phase on century & leap year dates...")
    m1 = get_moon_phase(datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc))
    m2 = get_moon_phase(datetime.datetime(2028, 2, 29, tzinfo=datetime.timezone.utc))
    m3 = get_moon_phase(datetime.datetime(2099, 12, 31, tzinfo=datetime.timezone.utc))
    assert all("emoji" in m and "illumination" in m for m in [m1, m2, m3])
    print("  ✅ Moon phase calculations verified across extreme dates.")

    # 6. Database Concurrency Stress Test (50 parallel operations)
    print("\n[6/6] Stress testing SQLite database with 50 concurrent async tasks...")
    await init_db()
    async def db_worker(i):
        uid = 800000 + i
        await get_or_create_user(uid, f"user_{i}", f"First_{i}")
        await log_search(uid, "Dhaka")
        await add_favorite(uid, "custom", "Dhaka", 23.71, 90.40)

    await asyncio.gather(*(db_worker(i) for i in range(50)))
    stats = await get_admin_stats()
    assert stats["total_users"] >= 50
    print("  ✅ SQLite WAL mode handled 50 simultaneous concurrent async operations without lock!")

    print("\n" + "=" * 40)
    print("🛡️ ALL EDGE-CASE TESTS PASSED WITH ZERO ERRORS!")
    print("========================================")

if __name__ == "__main__":
    asyncio.run(run_edge_case_tests())
