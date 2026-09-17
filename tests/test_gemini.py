"""
Automated Test Suite for Google Gemini AI Integration
Verifies general question answering, multi-turn memory, and intent routing.
"""
import sys
import asyncio
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from services.gemini_service import ask_gemini, clear_user_history
from services.nlp_parser import classify_intent

async def run_gemini_tests():
    print("=" * 45)
    print("🤖 Running Google Gemini AI Integration Tests")
    print("=" * 45)

    test_user_id = 999888777
    clear_user_history(test_user_id)

    # Test 1: General Knowledge Query
    print("\n[1/3] Testing General Knowledge Answering in Bengali...")
    q1 = "বাংলাদেশের জাতীয় ফলের নাম কী? সংক্ষেপে এক বাক্যে বলো।"
    ans1 = await ask_gemini(test_user_id, q1, "bn")
    print(f"  Q: {q1}")
    print(f"  A: {ans1.strip()}")
    assert len(ans1) > 5, "Gemini returned an empty or too short response"
    assert "কাঁঠাল" in ans1 or "jackfruit" in ans1.lower(), f"Unexpected answer: {ans1}"
    print("  ✅ General Knowledge Answering PASSED.")

    # Test 2: Multi-turn Chat Memory
    print("\n[2/3] Testing Multi-turn Chat Memory...")
    q2_turn1 = "আমার নাম রাহাত এবং আমি একজন প্রোগ্রামার।"
    ans2_turn1 = await ask_gemini(test_user_id, q2_turn1, "bn")
    print(f"  Turn 1 Q: {q2_turn1}")
    print(f"  Turn 1 A: {ans2_turn1[:100]}...")

    q2_turn2 = "আমার নাম কী মনে আছে?"
    ans2_turn2 = await ask_gemini(test_user_id, q2_turn2, "bn")
    print(f"  Turn 2 Q: {q2_turn2}")
    print(f"  Turn 2 A: {ans2_turn2.strip()}")
    assert "রাহাত" in ans2_turn2 or "rahat" in ans2_turn2.lower(), f"Memory failed to recall name: {ans2_turn2}"
    print("  ✅ Multi-turn Memory Retention PASSED.")

    # Test 3: Intent Classification Routing
    print("\n[3/3] Testing Weather vs Gemini Routing...")
    cases = [
        ("আজ কি বৃষ্টি হবে?", "rain"),
        ("ছাতা লাগবে কি?", "umbrella"),
        ("আজকে কেমন গরম?", "temp"),
        ("Dhaka", "general_weather"),
        ("পাইথনে একটি লিস্ট কীভাবে বানায়?", "unknown"),
        ("কেমন আছো তুমি?", "unknown"),
        ("একটি মজার হাসির কৌতুক বলো", "unknown")
    ]
    for text, expected_intent in cases:
        res = classify_intent(text)
        actual = res["intent"]
        assert actual == expected_intent, f"For '{text}', expected {expected_intent} but got {actual}"
        print(f"  Query: '{text}' -> Intent: {actual} (Expected: {expected_intent}) ✅")

    print("  ✅ Intent Classification Routing PASSED.")

    print("\n" + "=" * 45)
    print("🎉 ALL GEMINI AI TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 45)

if __name__ == "__main__":
    asyncio.run(run_gemini_tests())
