"""
Natural Language Processing & Intent Matcher for Weather Queries
Handles conversational questions in Bangla and English.
"""
import re
from typing import Optional, Tuple, Dict, Any

def normalize_bengali_name(word: str) -> str:
    """Strip common Bengali locative/possessive suffixes like -er, -yer, -te, -r, -e."""
    clean = word.strip("?,.!;:\"' ")
    for suffix in ['ের', 'য়ের', 'তে', 'র', 'য়', 'ে']:
        if clean.endswith(suffix) and len(clean) - len(suffix) >= 3:
            return clean[:-len(suffix)]
    return clean

# Comprehensive 64 districts, Dhaka/Chittagong neighborhoods & world cities
COMMON_CITY_ALIASES = {
    # Dhaka Division & Areas
    "ঢাকা": "Dhaka", "ঢাকায়": "Dhaka", "dhaka": "Dhaka",
    "মিরপুর": "Mirpur, Dhaka", "mirpur": "Mirpur, Dhaka",
    "উত্তরা": "Uttara, Dhaka", "uttara": "Uttara, Dhaka",
    "ধানমন্ডি": "Dhanmondi, Dhaka", "dhanmondi": "Dhanmondi, Dhaka",
    "গুলশান": "Gulshan, Dhaka", "gulshan": "Gulshan, Dhaka",
    "বনানী": "Banani, Dhaka", "banani": "Banani, Dhaka",
    "মতিঝিল": "Motijheel, Dhaka", "motijheel": "Motijheel, Dhaka",
    "তেজগাঁও": "Tejgaon, Dhaka", "tejgaon": "Tejgaon, Dhaka",
    "সাভার": "Savar", "savar": "Savar",
    "টঙ্গী": "Tongi", "tongi": "Tongi",
    "কেরানীগঞ্জ": "Keraniganj", "keraniganj": "Keraniganj",
    "গাজীপুর": "Gazipur", "gazipur": "Gazipur",
    "নারায়ণগঞ্জ": "Narayanganj", "narayanganj": "Narayanganj",
    "নরসিংদী": "Narsingdi", "narsingdi": "Narsingdi",
    "টাঙ্গাইল": "Tangail", "tangail": "Tangail",
    "কিশোরগঞ্জ": "Kishoreganj", "kishoreganj": "Kishoreganj",
    "মানিকগঞ্জ": "Manikganj", "manikganj": "Manikganj",
    "মুন্সীগঞ্জ": "Munshiganj", "munshiganj": "Munshiganj",
    "মুন্সিগঞ্জ": "Munshiganj",
    "ফরিদপুর": "Faridpur", "faridpur": "Faridpur",
    "গোপালগঞ্জ": "Gopalganj", "gopalganj": "Gopalganj",
    "মাদারীপুর": "Madaripur", "madaripur": "Madaripur",
    "রাজবাড়ী": "Rajbari", "rajbari": "Rajbari", "রাজবাড়ি": "Rajbari",
    "শরীয়তপুর": "Shariatpur", "shariatpur": "Shariatpur",

    # Chittagong Division
    "চট্টগ্রাম": "Chittagong", "চিটাগাং": "Chittagong", "chittagong": "Chittagong", "chattogram": "Chittagong",
    "কক্সবাজার": "Cox's Bazar", "cox's bazar": "Cox's Bazar", "coxs bazar": "Cox's Bazar",
    "কুমিল্লা": "Comilla", "comilla": "Comilla", "cumilla": "Comilla",
    "ফেনী": "Feni", "feni": "Feni",
    "ব্রাহ্মণবাড়িয়া": "Brahmanbaria", "brahmanbaria": "Brahmanbaria", "ব্রাহ্মণবাড়িয়া": "Brahmanbaria",
    "নোয়াখালী": "Noakhali", "noakhali": "Noakhali", "নোয়াখালী": "Noakhali",
    "চাঁদপুর": "Chandpur", "chandpur": "Chandpur",
    "লক্ষ্মীপুর": "Lakshmipur", "lakshmipur": "Lakshmipur",
    "রাঙ্গামাটি": "Rangamati", "rangamati": "Rangamati", "রাঙামাটি": "Rangamati",
    "খাগড়াছড়ি": "Khagrachhari", "khagrachhari": "Khagrachhari", "খাগড়াছড়ি": "Khagrachhari",
    "বান্দরবান": "Bandarban", "bandarban": "Bandarban",
    "টেকনাফ": "Teknaf", "teknaf": "Teknaf",
    "সাজেক": "Sajek", "sajek": "Sajek",

    # Sylhet Division
    "সিলেট": "Sylhet", "sylhet": "Sylhet",
    "মৌলভীবাজার": "Moulvibazar", "moulvibazar": "Moulvibazar",
    "শ্রীমঙ্গল": "Srimangal", "srimangal": "Srimangal", "sreemangal": "Srimangal",
    "হবিগঞ্জ": "Habiganj", "habiganj": "Habiganj",
    "সুনামগঞ্জ": "Sunamganj", "sunamganj": "Sunamganj",

    # Rajshahi Division
    "রাজশাহী": "Rajshahi", "rajshahi": "Rajshahi",
    "বগুড়া": "Bogra", "bogra": "Bogra", "বগুড়া": "Bogra", "bogura": "Bogra",
    "পাবনা": "Pabna", "pabna": "Pabna",
    "সিরাজগঞ্জ": "Sirajganj", "sirajganj": "Sirajganj",
    "নাটোর": "Natore", "natore": "Natore",
    "নওগাঁ": "Naogaon", "naogaon": "Naogaon",
    "চাঁপাইনবাবগঞ্জ": "Chapai Nawabganj", "chapai nawabganj": "Chapai Nawabganj",
    "জয়পুরহাট": "Joypurhat", "joypurhat": "Joypurhat", "জয়পুরহাট": "Joypurhat",
    "ঈশ্বরদী": "Ishwardi", "ishwardi": "Ishwardi",

    # Khulna Division
    "খুলনা": "Khulna", "khulna": "Khulna",
    "যশোর": "Jessore", "jessore": "Jessore", "jashore": "Jessore",
    "কুষ্টিয়া": "Kushtia", "কুষ্টিয়া": "Kushtia", "kushtia": "Kushtia",
    "ঝিনাইদহ": "Jhenaidah", "jhenaidah": "Jhenaidah",
    "সাতক্ষীরা": "Satkhira", "satkhira": "Satkhira",
    "বাগেরহাট": "Bagerhat", "bagerhat": "Bagerhat",
    "চুয়াডাঙ্গা": "Chuadanga", "chuadanga": "Chuadanga", "চুয়াডাঙ্গা": "Chuadanga",
    "মেহেরপুর": "Meherpur", "meherpur": "Meherpur",
    "মাগুরা": "Magura", "magura": "Magura",
    "নড়াইল": "Narail", "narail": "Narail", "নড়াইল": "Narail",
    "ভেড়ামারা": "Bheramara", "bheramara": "Bheramara",

    # Barishal Division
    "বরিশাল": "Barisal", "barisal": "Barisal", "barishal": "Barisal",
    "পটুয়াখালী": "Patuakhali", "patuakhali": "Patuakhali", "পটুয়াখালী": "Patuakhali",
    "ভোলা": "Bhola", "bhola": "Bhola",
    "পিরোজপুর": "Pirojpur", "pirojpur": "Pirojpur",
    "বরগুনা": "Barguna", "barguna": "Barguna",
    "ঝালকাঠি": "Jhalokati", "jhalokati": "Jhalokati",
    "কুয়াকাটা": "Kuakata", "kuakata": "Kuakata",

    # Rangpur Division
    "রংপুর": "Rangpur", "rangpur": "Rangpur",
    "দিনাজপুর": "Dinajpur", "dinajpur": "Dinajpur",
    "কুড়িগ্রাম": "Kurigram", "kurigram": "Kurigram", "কুড়িগ্রাম": "Kurigram",
    "গাইবান্ধা": "Gaibandha", "gaibandha": "Gaibandha",
    "নীলফামারী": "Nilphamari", "nilphamari": "Nilphamari",
    "লালমনিরহাট": "Lalmonirhat", "lalmonirhat": "Lalmonirhat",
    "পঞ্চগড়": "Panchagarh", "panchagarh": "Panchagarh", "পঞ্চগড়": "Panchagarh",
    "ঠাকুরগাঁও": "Thakurgaon", "thakurgaon": "Thakurgaon",
    "সৈয়দপুর": "Saidpur", "saidpur": "Saidpur",

    # Mymensingh Division
    "ময়মনসিংহ": "Mymensingh", "mymensingh": "Mymensingh",
    "জামালপুর": "Jamalpur", "jamalpur": "Jamalpur",
    "নেত্রকোনা": "Netrokona", "netrokona": "Netrokona",
    "শেরপুর": "Sherpur", "sherpur": "Sherpur",

    # World Cities
    "লন্ডন": "London", "london": "London",
    "নিউইয়র্ক": "New York", "new york": "New York",
    "দিল্লি": "Delhi", "delhi": "Delhi",
    "কলকাতা": "Kolkata", "kolkata": "Kolkata",
    "দুবাই": "Dubai", "dubai": "Dubai",
    "টোকিও": "Tokyo", "tokyo": "Tokyo",
    "প্যারিস": "Paris", "paris": "Paris",
    "মক্কা": "Mecca", "মদিনা": "Medina"
}

def extract_city_from_text(text: str) -> Optional[str]:
    """Scan text for known city mentions with multi-word priority and suffix normalization."""
    lower = text.lower().strip()

    # 1. Direct match
    if lower in COMMON_CITY_ALIASES:
        return COMMON_CITY_ALIASES[lower]

    # 2. Normalized direct match
    norm_direct = normalize_bengali_name(lower)
    if norm_direct in COMMON_CITY_ALIASES:
        return COMMON_CITY_ALIASES[norm_direct]

    # 3. Multi-word alias check (longest key first)
    sorted_aliases = sorted(COMMON_CITY_ALIASES.keys(), key=len, reverse=True)
    for alias in sorted_aliases:
        if len(alias) >= 3 and alias in lower:
            return COMMON_CITY_ALIASES[alias]

    # 4. Word-by-word with Bengali inflection normalization
    words = re.findall(r"[\u0980-\u09FFa-zA-Z]+", text)
    for w in words:
        w_lower = w.lower()
        if w_lower in COMMON_CITY_ALIASES:
            return COMMON_CITY_ALIASES[w_lower]
        w_norm = normalize_bengali_name(w_lower)
        if w_norm in COMMON_CITY_ALIASES:
            return COMMON_CITY_ALIASES[w_norm]

    return None

def detect_travel_query(text: str) -> Optional[Tuple[str, str]]:
    """Detect if message is a travel route query like 'Dhaka to Sylhet' or 'Dhaka -> Cox's Bazar'."""
    pattern = r"([a-zA-Z\u0980-\u09FF\s']+)\s*(?:to|থেকে|->|—>)\s*([a-zA-Z\u0980-\u09FF\s']+)"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        orig = match.group(1).strip()
        dest = match.group(2).strip()
        # Ensure they are valid names, not standard greeting words
        if len(orig) >= 3 and len(dest) >= 3 and "weather" not in orig.lower() and "weather" not in dest.lower():
            # Resolve aliases if any
            orig = COMMON_CITY_ALIASES.get(orig.lower(), orig)
            dest = COMMON_CITY_ALIASES.get(dest.lower(), dest)
            return orig, dest
    return None

def classify_intent(text: str) -> Dict[str, Any]:
    """
    Classifies the user's conversational intent.
    Returns:
    {
        "intent": "rain" | "umbrella" | "temp" | "outdoor" | "wind" | "aqi" | "travel" | "explain" | "general_weather",
        "city": Optional[str],
        "term": Optional[str]
    }
    """
    lower = text.lower().strip()
    city = extract_city_from_text(text)

    # Travel check
    travel_route = detect_travel_query(text)
    if travel_route:
        return {
            "intent": "travel",
            "origin": travel_route[0],
            "destination": travel_route[1],
            "city": travel_route[1]
        }

    # Terminology explanation intent
    if any(k in lower for k in ["humidity কী", "আর্দ্রতা কী", "what is humidity", "humidity মানে কী"]):
        return {"intent": "explain", "term": "humidity", "city": city}
    if any(k in lower for k in ["aqi কী", "এয়ার কোয়ালিটি কী", "what is aqi", "aqi মানে কী"]):
        return {"intent": "explain", "term": "aqi", "city": city}
    if any(k in lower for k in ["uv কী", "ইউভি কী", "what is uv", "uv index কী"]):
        return {"intent": "explain", "term": "uv", "city": city}
    if any(k in lower for k in ["dew point কী", "শিশিরাঙ্ক কী", "what is dew point"]):
        return {"intent": "explain", "term": "dew_point", "city": city}

    # Umbrella intent
    if any(k in lower for k in ["ছাতা", "ছাতা লাগবে", "umbrella", "need umbrella"]):
        return {"intent": "umbrella", "city": city}

    # Rain intent
    if any(k in lower for k in ["বৃষ্টি", "বৃষ্টি হবে", "rain", "raining", "rain chance"]):
        return {"intent": "rain", "city": city}

    # Heat / Cold / Temperature intent
    if any(k in lower for k in ["গরম", "ঠান্ডা", "শীত", "তাপমাত্রা", "hot", "cold", "temperature"]):
        return {"intent": "temp", "city": city}

    # Outdoor / Walking intent
    if any(k in lower for k in ["বাইরে যাওয়া", "বাইরে যাওয়া যাবে", "হাঁটতে", "go outside", "outdoor", "walking"]):
        return {"intent": "outdoor", "city": city}

    # Wind intent
    if any(k in lower for k in ["বাতাস", "ঝড়", "wind", "windy", "storm"]):
        return {"intent": "wind", "city": city}

    # AQI / Air Quality
    if any(k in lower for k in ["বাতাসের মান", "ধোঁয়াশা", "ধূলাবালি", "air quality", "pollution"]):
        return {"intent": "aqi", "city": city}

    # General Weather intent (explicit keywords or real-time keywords)
    weather_keywords = [
        "আবহাওয়া", "আবহাওয়ার", "আবহাওয়া", "আবহাওয়ার",
        "ওয়েদার", "ওয়েদার", "আজকের ওয়েদার", "আজকে কেমন", "weather",
        "রিয়েল-টাইম", "রিয়েল-টাইম", "রিয়েল টাইম", "রিয়েল টাইম", "real-time", "realtime"
    ]
    if any(k in lower for k in weather_keywords):
        return {"intent": "general_weather", "city": city}

    # If it's solely a known city name or alias (e.g. "Dhaka", "ঢাকা", "সিলেট", "মিরপুর")
    if lower in COMMON_CITY_ALIASES:
        return {"intent": "general_weather", "city": COMMON_CITY_ALIASES[lower]}

    norm_lower = normalize_bengali_name(lower)
    if norm_lower in COMMON_CITY_ALIASES:
        return {"intent": "general_weather", "city": COMMON_CITY_ALIASES[norm_lower]}

    return {"intent": "unknown", "city": city}
