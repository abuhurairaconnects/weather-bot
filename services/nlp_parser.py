"""
Natural Language Processing & Intent Matcher for Weather Queries
Handles conversational questions in Bangla and English.
"""
import re
from typing import Optional, Tuple, Dict, Any

# Known major cities in Bangladesh & world for quick pattern matching
COMMON_CITY_ALIASES = {
    "ঢাকা": "Dhaka",
    "ঢাকায়": "Dhaka",
    "dhaka": "Dhaka",
    "চট্টগ্রাম": "Chittagong",
    "চিটাগাং": "Chittagong",
    "chittagong": "Chittagong",
    "সিলেট": "Sylhet",
    "সিলেটে": "Sylhet",
    "sylhet": "Sylhet",
    "রাজশাহী": "Rajshahi",
    "rajshahi": "Rajshahi",
    "খুলনা": "Khulna",
    "khulna": "Khulna",
    "বরিশাল": "Barisal",
    "barisal": "Barisal",
    "রংপুর": "Rangpur",
    "rangpur": "Rangpur",
    "ময়মনসিংহ": "Mymensingh",
    "mymensingh": "Mymensingh",
    "কক্সবাজার": "Cox's Bazar",
    "কক্সবাজারে": "Cox's Bazar",
    "cox's bazar": "Cox's Bazar",
    "coxs bazar": "Cox's Bazar",
    "কুমিল্লা": "Comilla",
    "comilla": "Comilla",
    "গাজীপুর": "Gazipur",
    "gazipur": "Gazipur",
    "নারায়ণগঞ্জ": "Narayanganj",
    "narayanganj": "Narayanganj",
    "বগুড়া": "Bogra",
    "bogra": "Bogra",
    "লন্ডন": "London",
    "london": "London",
    "নিউইয়র্ক": "New York",
    "new york": "New York",
    "দিল্লি": "Delhi",
    "delhi": "Delhi",
    "কলকাতা": "Kolkata",
    "kolkata": "Kolkata",
    "দুবাই": "Dubai",
    "dubai": "Dubai"
}

def extract_city_from_text(text: str) -> Optional[str]:
    """Scan text for known city mentions."""
    lower = text.lower()
    for alias, standard_name in COMMON_CITY_ALIASES.items():
        if alias in lower:
            return standard_name
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

    # General Weather intent
    if any(k in lower for k in ["আবহাওয়া", "ওয়েদার", "আজকের ওয়েদার", "আজকে কেমন", "weather"]):
        return {"intent": "general_weather", "city": city}

    # If it's just a city name
    if city and len(lower) < 25:
        return {"intent": "general_weather", "city": city}

    return {"intent": "unknown", "city": city}
