import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding='utf-8')
from services.bd_geocoder import find_bd_location

test_queries = [
    'Tarash', 'তাড়াশ', 'তারাশ', 'তাড়াশের আবহাওয়া', 'তাড়াশ উপজেলা',
    'Singra', 'সিংড়া', 'সিংড়া নাটোর', 'singra natore',
    'Chilmari', 'চিলমারী', 'চিলমারীর আবহাওয়া',
    'Pekua', 'পেকুয়া', 'পেকুয়া উপজেলা',
    'Dhaka', 'ঢাকা', 'মিরপুর', 'উত্তরা',
    'Chittagong', 'চট্টগ্রাম', 'চিটাগাং', 'টেকনাফ',
    'Bogra', 'বগুড়া', 'বগুড়া', 'বগুড়া জেলা',
    'Sirajganj', 'সিরাজগঞ্জ',
    'Sreemangal', 'শ্রীমঙ্গল', 'কুষ্টিয়া', 'ভেড়ামারা',
    'Galachipa', 'গলাচিপা', 'বোরহানউদ্দিন', 'দেবিদ্বার',
    'ভুরুঙ্গামারী', 'রৌমারী', 'মহেশখালী'
]

passed = 0
for q in test_queries:
    res = find_bd_location(q)
    if res:
        name = res["name"]
        disp = res["display_name"]
        lat = res["lat"]
        lon = res["lon"]
        print(f"✅ PASS: {q:20} -> {name:15} ({disp}) [{lat}, {lon}]")
        passed += 1
    else:
        print(f"❌ FAIL: {q}")

print(f"\nTotal passed: {passed}/{len(test_queries)}")
assert passed == len(test_queries), f"Expected all {len(test_queries)} to pass, got {passed}"
