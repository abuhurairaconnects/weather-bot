import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding='utf-8')

from services.nlp_parser import classify_intent, extract_city_from_text

test_cases = [
    ("তাড়াশের আবহাওয়া", "Tarash", "general_weather"),
    ("তাড়াশ", "Tarash", "general_weather"),
    ("tarash", "Tarash", "general_weather"),
    ("সিংড়ায় কি বৃষ্টি হবে?", "Singra", "rain"),
    ("পেকুয়াতে কি ছাতা লাগবে?", "Pekua", "umbrella"),
    ("চিলমারীর তাপমাত্রা কত?", "Chilmari", "temp"),
    ("বোরহানউদ্দিনের আবহাওয়া", "Burhanuddin", "general_weather"),
    ("দেবিদ্বার উপজেলা", "Debidwar", "general_weather"),
    ("রৌমারীর খবর কি", "Rowmari", "general_weather"),
    ("Dhaka weather", "Dhaka", "general_weather"),
    ("সিরাজগঞ্জ", "Sirajgonj", "general_weather"),
    ("বগুড়া", "Bogura", "general_weather"),
    ("শ্রীমঙ্গল", "Sreemangal", "general_weather")
]

passed = 0
for text, exp_city, exp_intent in test_cases:
    res = classify_intent(text)
    city = res.get("city")
    intent = res.get("intent")
    city_match = (city and exp_city.lower() in city.lower())
    intent_match = (intent == exp_intent)
    
    if city_match and intent_match:
        print(f"✅ PASS: '{text}' -> City: {city}, Intent: {intent}")
        passed += 1
    else:
        print(f"❌ FAIL: '{text}' -> Expected ({exp_city}, {exp_intent}), got ({city}, {intent})")

print(f"\nNLP Tests: {passed}/{len(test_cases)} passed")
assert passed == len(test_cases), f"Expected {len(test_cases)} passed, got {passed}"
