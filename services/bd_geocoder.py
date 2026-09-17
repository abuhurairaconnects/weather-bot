"""
Comprehensive Bangladesh Geocoder & Administrative Location Index.
Covers all 64 districts, all 495+ upazilas, and major metropolitan thanas (672 locations)
with exact GPS coordinates, bilingual names, and robust phonetic/suffix matching.
"""
import json
import os
import re
import unicodedata
from typing import Optional, Dict, Any, List, Set

_BD_LOCATIONS: List[Dict[str, Any]] = []
_EXACT_INDEX: Dict[str, Dict[str, Any]] = {}
_NORMALIZED_INDEX: Dict[str, Dict[str, Any]] = {}
_ALL_KEYWORDS: Set[str] = set()

_DIVISIONS_LIST: List[Dict[str, str]] = [
    {"id": "Dhaka", "en": "Dhaka", "bn": "ঢাকা"},
    {"id": "Chattogram", "en": "Chattogram", "bn": "চট্টগ্রাম"},
    {"id": "Rajshahi", "en": "Rajshahi", "bn": "রাজশাহী"},
    {"id": "Khulna", "en": "Khulna", "bn": "খুলনা"},
    {"id": "Barishal", "en": "Barishal", "bn": "বরিশাল"},
    {"id": "Sylhet", "en": "Sylhet", "bn": "সিলেট"},
    {"id": "Rangpur", "en": "Rangpur", "bn": "রংপুর"},
    {"id": "Mymensingh", "en": "Mymensingh", "bn": "ময়মনসিংহ"},
]

DISTRICT_NAME_CANONICAL: Dict[str, str] = {
    "chittagong": "Chattogram",
    "chattogram": "Chattogram",
    "bogra": "Bogura",
    "bogura": "Bogura",
    "jessore": "Jashore",
    "jashore": "Jashore",
    "barisal": "Barishal",
    "barishal": "Barishal",
    "comilla": "Cumilla",
    "cumilla": "Cumilla",
    "khagrachari": "Khagrachhari",
    "khagrachhari": "Khagrachhari",
    "sirajganj": "Sirajgonj",
    "sirajgonj": "Sirajgonj",
    "moulvibazar": "Maulvibazar",
    "maulvibazar": "Maulvibazar",
    "coxsbazar": "Cox's Bazar",
    "cox's bazar": "Cox's Bazar",
}

_DISTRICTS_BY_DIV: Dict[str, List[Dict[str, str]]] = {}
_UPAZILAS_BY_DIST: Dict[str, List[Dict[str, Any]]] = {}

COMMON_BD_SPELLING_VARIANTS = {
    # English variations
    "sirajganj": "sirajgonj",
    "sirajgonj": "sirajgonj",
    "bogra": "bogura",
    "bogura": "bogura",
    "chittagong": "chattogram",
    "chattogram": "chattogram",
    "jessore": "jashore",
    "jashore": "jashore",
    "barisal": "barishal",
    "barishal": "barishal",
    "comilla": "cumilla",
    "cumilla": "cumilla",
    "coxs bazar": "cox's bazar",
    "coxsbazar": "cox's bazar",
    "srimangal": "sreemangal",
    "sreemangal": "sreemangal",
    "sreemongol": "sreemangal",
    "saidpur": "syedpur",
    "syedpur": "syedpur",
    "chapainawabganj": "chapai nawabganj",
    "moulvibazar": "maulvibazar",
    "moulvi bazar": "maulvibazar",
    "brahmanbaria": "brahmanbaria",
    "b-baria": "brahmanbaria",
    "bbaria": "brahmanbaria",
    "borhanuddin": "burhanuddin",
    "burhanuddin": "burhanuddin",
    "chilmari": "chilmari",
    "tarash": "tarash",
    "pekua": "pekua",
    "singra": "singra",
    "roumari": "rowmari",
    "rowmari": "rowmari",
    "tentulia": "tetulia",
    "tetulia": "tetulia",
    "barora": "barura",
    "barura": "barura",
    # Bengali variations
    "বরুড়া": "বড়ুরা",
    "বরুড়া": "বড়ুরা",
    "বরোড়া": "বড়ুরা",
    "বরোড়া": "বড়ুরা",
    "বড়ুড়া": "বড়ুরা",
    "বড়ুড়া": "বড়ুরা",
    "বরুরা": "বড়ুরা",
    "চিটাগাং": "চট্টগ্রাম",
    "যশোহর": "যশোর",
    "বরিশাল": "বরিশাল",
    "কুষ্টিয়া": "কুষ্টিয়া",
    "চাটমহর": "চাটমোহর",
    "তারাশ": "তাড়াশ",
    "তাড়াশ": "তাড়াশ",
    "তাড়াশ": "তাড়াশ",
    "বগুড়া": "বগুড়া",
    "বগুড়া": "বগুড়া",
    "সিংড়া": "সিংড়া",
    "সিংড়া": "সিংড়া",
    "কুড়িগ্রাম": "কুড়িগ্রাম",
    "কুড়িগ্রাম": "কুড়িগ্রাম",
    "ভেড়ামারা": "ভেড়ামারা",
    "বোরহানউদ্দিন": "বুরহানউদ্দিন",
    "বোরহান উদ্দিন": "বুরহানউদ্দিন",
    "বোরহান উদ্দীন": "বুরহানউদ্দিন",
    "রৌমারী": "রউমারি",
    "রৌমারি": "রউমারি",
}

def normalize_bn_unicode(text: str) -> str:
    """Normalize Bengali unicode characters, nuktas, and decomposed glyphs."""
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    # Unify nukta representations: ড + ় -> ড় (U+09DC), ঢ + ় -> ঢ় (U+09DD), য + ় -> য় (U+09DF)
    text = text.replace("\u09a1\u09bc", "\u09dc")
    text = text.replace("\u09a2\u09bc", "\u09dd")
    text = text.replace("\u09af\u09bc", "\u09df")
    return text.strip()

def strip_bd_affixes(text: str) -> str:
    """Strip administrative words (উপজেলা, জেলা, thana, etc.) and grammatical suffixes."""
    admin_qualifiers = [
        "উপজেলা", "জেলা", "থানা", "সদর", "পৌরসভা", "বিভাগ",
        "রিয়েল-টাইম", "রিয়েল-টাইম", "রিয়েল টাইম", "রিয়েল টাইম",
        "ওয়েদার", "ওয়েদার", "ওয়েদারের", "ওয়েদারের",
        "আবহাওয়া", "আবহাওয়া", "আবহাওয়ার", "আবহাওয়ার",
        "আজকের", "এখনকার", "বর্তমান",
        "upazila", "district", "thana", "sadar", "division", "weather", "forecast", "realtime", "real-time"
    ]
    cleaned = text
    for q in admin_qualifiers:
        cleaned = re.sub(r'(?i)\b' + re.escape(q) + r'\b', ' ', cleaned)
        cleaned = cleaned.replace(q, ' ')

    cleaned = cleaned.strip("?,.!;:\"' ")
    
    # Strip Bengali grammatical suffixes (locative, possessive)
    for suffix in ['ের', 'য়ের', 'তে', 'র', 'য়', 'ে', 'এ']:
        if cleaned.endswith(suffix) and len(cleaned) - len(suffix) >= 3:
            cleaned = cleaned[:-len(suffix)]
            break

    return cleaned.strip()

def normalize_key(text: str) -> str:
    """
    Produce a canonical search key by standardizing:
    - Case & whitespace/punctuation
    - English: 'gonj' -> 'ganj', 'pore' -> 'pur'
    - Bengali: 'ী' -> 'ি', 'ূ' -> 'ু', 'ড়'/'ড়' -> 'র'
    """
    if not text:
        return ""
    s = normalize_bn_unicode(text).lower()
    # English normalization
    s = s.replace("gonj", "ganj")
    s = s.replace("pore", "pur")
    # Bengali vowel and nukta normalization
    s = s.replace("ী", "ি")
    s = s.replace("ূ", "ু")
    s = s.replace("ড়", "র")
    s = s.replace("ড়", "র")
    s = s.replace("ঢ়", "র")
    s = s.replace("ঢ়", "র")
    s = s.replace("ণ", "ন")
    s = s.replace("ঁ", "")
    # Remove all non-alphanumeric and non-Bengali
    s = re.sub(r'[^a-zA-Z0-9\u0980-\u09FF]', '', s)
    return s

def _load_locations():
    """Load and index all Bangladesh locations into memory."""
    global _BD_LOCATIONS, _EXACT_INDEX, _NORMALIZED_INDEX, _ALL_KEYWORDS
    global _DISTRICTS_BY_DIV, _UPAZILAS_BY_DIST
    if _BD_LOCATIONS:
        return  # Already loaded

    _DISTRICTS_BY_DIV = {d["en"]: [] for d in _DIVISIONS_LIST}
    _UPAZILAS_BY_DIST = {}
    seen_districts = set()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(base_dir, "data", "bd_locations.json")
    if not os.path.exists(json_path):
        return

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            _BD_LOCATIONS = json.load(f)
    except Exception as e:
        print(f"Error loading bd_locations.json: {e}")
        return

    for loc in _BD_LOCATIONS:
        name_en = loc.get("name_en", "").strip()
        name_bn = normalize_bn_unicode(loc.get("name_bn", "").strip())
        dist_en = loc.get("district_en", "").strip()
        dist_bn = normalize_bn_unicode(loc.get("district_bn", "").strip())
        is_district = loc.get("type") == "district"
        div_en = loc.get("division_en", "").strip()
        canon_dist = DISTRICT_NAME_CANONICAL.get(dist_en.lower(), dist_en)

        if is_district:
            display_name = f"{name_bn} ({name_en}), {loc.get('division_bn', '')} বিভাগ"
            if canon_dist not in seen_districts and div_en in _DISTRICTS_BY_DIV:
                seen_districts.add(canon_dist)
                _DISTRICTS_BY_DIV[div_en].append({
                    "id": canon_dist,
                    "name_en": canon_dist,
                    "name_bn": name_bn,
                    "division_en": div_en,
                    "division_bn": loc.get("division_bn", "")
                })
        else:
            display_name = f"{name_bn} ({name_en}), {dist_bn}"
            if canon_dist:
                if canon_dist not in _UPAZILAS_BY_DIST:
                    _UPAZILAS_BY_DIST[canon_dist] = []
                _UPAZILAS_BY_DIST[canon_dist].append({
                    "name_en": name_en,
                    "name_bn": name_bn,
                    "district_en": canon_dist,
                    "district_bn": dist_bn,
                    "division_en": div_en,
                    "division_bn": loc.get("division_bn", ""),
                    "lat": float(loc["lat"]),
                    "lon": float(loc["lon"])
                })

        standard_entry = {
            "name": name_en,
            "display_name": display_name,
            "lat": float(loc["lat"]),
            "lon": float(loc["lon"]),
            "country": "Bangladesh",
            "timezone": "Asia/Dhaka",
            "type": loc.get("type", "upazila"),
            "district": dist_en,
            "district_bn": dist_bn,
            "division": loc.get("division_en", ""),
            "division_bn": loc.get("division_bn", "")
        }

        # Index by English lowercase
        en_key = name_en.lower()
        if en_key not in _EXACT_INDEX or is_district:
            _EXACT_INDEX[en_key] = standard_entry

        # Index by canonical normalized key
        en_norm = normalize_key(name_en)
        if en_norm and (en_norm not in _NORMALIZED_INDEX or is_district):
            _NORMALIZED_INDEX[en_norm] = standard_entry

        # Index by Bengali name
        if name_bn:
            if name_bn not in _EXACT_INDEX or is_district:
                _EXACT_INDEX[name_bn] = standard_entry

            bn_norm = normalize_key(name_bn)
            if bn_norm and (bn_norm not in _NORMALIZED_INDEX or is_district):
                _NORMALIZED_INDEX[bn_norm] = standard_entry

        # Track keywords for NLP
        _ALL_KEYWORDS.add(name_en.lower())
        if name_bn:
            _ALL_KEYWORDS.add(name_bn)

    # Sort districts and upazilas alphabetically by Bengali name
    for d_en in _DISTRICTS_BY_DIV:
        _DISTRICTS_BY_DIV[d_en].sort(key=lambda x: x["name_bn"])
    for dt_en in _UPAZILAS_BY_DIST:
        _UPAZILAS_BY_DIST[dt_en].sort(key=lambda x: x["name_bn"])

    # Pre-index known aliases
    for alias, target in COMMON_BD_SPELLING_VARIANTS.items():
        alias_norm = normalize_key(alias)
        target_norm = normalize_key(target)
        if target_norm in _NORMALIZED_INDEX and alias_norm not in _NORMALIZED_INDEX:
            _NORMALIZED_INDEX[alias_norm] = _NORMALIZED_INDEX[target_norm]
        target_exact = target.lower()
        if target_exact in _EXACT_INDEX:
            alias_exact = alias.lower()
            if alias_exact not in _EXACT_INDEX:
                _EXACT_INDEX[alias_exact] = _EXACT_INDEX[target_exact]

# Initial load on import
_load_locations()

def get_all_divisions() -> List[Dict[str, str]]:
    """Return list of all 8 administrative divisions of Bangladesh."""
    return _DIVISIONS_LIST

def get_districts_by_division(division_en: str) -> List[Dict[str, str]]:
    """Return all districts belonging to a specific division."""
    _load_locations()
    for d, dist_list in _DISTRICTS_BY_DIV.items():
        if d.lower() == division_en.lower():
            return dist_list
    return []

def get_upazilas_by_district(district_en: str) -> List[Dict[str, Any]]:
    """Return all upazilas belonging to a specific district."""
    _load_locations()
    canon = DISTRICT_NAME_CANONICAL.get(district_en.lower(), district_en)
    for d, upz_list in _UPAZILAS_BY_DIST.items():
        if d.lower() == canon.lower():
            return upz_list
    return []

def find_bd_location(query: str) -> Optional[Dict[str, Any]]:
    """
    Search local index for any of the 64 districts or 495+ upazilas in Bangladesh.
    Matches English and Bengali names, handles inflections, suffixes, and qualifiers.
    Returns matched location dict with lat, lon, display_name or None if not found.
    """
    if not query:
        return None

    _load_locations()

    raw_query = query.strip()
    norm_query = normalize_bn_unicode(raw_query)
    lower_query = norm_query.lower()

    # 1. Exact string lookup
    if lower_query in _EXACT_INDEX:
        return _EXACT_INDEX[lower_query]

    # 2. Canonical normalized lookup
    k_query = normalize_key(lower_query)
    if k_query in _NORMALIZED_INDEX:
        return _NORMALIZED_INDEX[k_query]

    # 3. Strip qualifiers & grammatical suffixes
    stripped = strip_bd_affixes(norm_query)
    if stripped and stripped != norm_query:
        s_lower = stripped.lower()
        if s_lower in _EXACT_INDEX:
            return _EXACT_INDEX[s_lower]

        s_norm = normalize_key(s_lower)
        if s_norm in _NORMALIZED_INDEX:
            return _NORMALIZED_INDEX[s_norm]

    # 4. Multi-word token lookup (e.g. "সিংড়া নাটোর", "Tarash Sirajganj", "তাড়াশের আবহাওয়া")
    words = re.findall(r'[\u0980-\u09FFa-zA-Z]+', norm_query)
    for w in words:
        w_clean = strip_bd_affixes(w)
        w_norm = normalize_key(w_clean)
        if len(w_norm) >= 2 and w_norm in _NORMALIZED_INDEX:
            return _NORMALIZED_INDEX[w_norm]

    return None

def is_bd_location(text: str) -> bool:
    """Check if the word or phrase corresponds to a valid Bangladesh location."""
    return find_bd_location(text) is not None

def get_all_bd_keywords() -> Set[str]:
    """Return all known keywords for NLP extraction."""
    _load_locations()
    return _ALL_KEYWORDS
