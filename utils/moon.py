"""
Moon phase calculation utility using the synodic cycle.
Accurately estimates moon age and phase without external API dependencies.
"""
import datetime
from typing import Dict

def get_moon_phase(dt: datetime.datetime = None) -> Dict[str, str]:
    """
    Calculate the moon phase for a given date.
    Returns a dictionary with 'emoji', 'name_en', 'name_bn', and 'illumination_percent'.
    """
    if dt is None:
        dt = datetime.datetime.now(datetime.timezone.utc)
        
    year = dt.year
    month = dt.month
    day = dt.day

    if month < 3:
        year -= 1
        month += 12

    a = year // 100
    b = a // 4
    c = 2 - a + b
    e = int(365.25 * (year + 4716))
    f = int(30.6001 * (month + 1))
    jd = c + day + e + f - 1524.5

    # Known new moon reference: Jan 6, 2000, 18:14 UTC (JD 2451549.5)
    synodic_month = 29.53058867
    days_since_new = (jd - 2451549.5) % synodic_month
    phase_ratio = days_since_new / synodic_month

    # Illumination approx
    import math
    illumination = (1 - math.cos(phase_ratio * 2 * math.pi)) / 2 * 100

    if phase_ratio < 0.03 or phase_ratio >= 0.97:
        return {
            "emoji": "🌑",
            "name_en": "New Moon",
            "name_bn": "নতুন চাঁদ (অমাবস্যা)",
            "illumination": f"{illumination:.0f}%"
        }
    elif phase_ratio < 0.22:
        return {
            "emoji": "🌒",
            "name_en": "Waxing Crescent",
            "name_bn": "শুক্লপক্ষ ক্রিসেন্ট (হিলাল)",
            "illumination": f"{illumination:.0f}%"
        }
    elif phase_ratio < 0.28:
        return {
            "emoji": "🌓",
            "name_en": "First Quarter",
            "name_bn": "প্রথম চতুর্থাংশ (অর্ধচন্দ্র)",
            "illumination": f"{illumination:.0f}%"
        }
    elif phase_ratio < 0.47:
        return {
            "emoji": "🌔",
            "name_en": "Waxing Gibbous",
            "name_bn": "শুক্লপক্ষ উত্তল চাঁদ",
            "illumination": f"{illumination:.0f}%"
        }
    elif phase_ratio < 0.53:
        return {
            "emoji": "🌕",
            "name_en": "Full Moon",
            "name_bn": "পূর্ণিমা (ভরা চাঁদ)",
            "illumination": f"{illumination:.0f}%"
        }
    elif phase_ratio < 0.72:
        return {
            "emoji": "🌖",
            "name_en": "Waning Gibbous",
            "name_bn": "কৃষ্ণপক্ষ উত্তল চাঁদ",
            "illumination": f"{illumination:.0f}%"
        }
    elif phase_ratio < 0.78:
        return {
            "emoji": "🌗",
            "name_en": "Last Quarter",
            "name_bn": "শেষ চতুর্থাংশ (অর্ধচন্দ্র)",
            "illumination": f"{illumination:.0f}%"
        }
    else:
        return {
            "emoji": "🌘",
            "name_en": "Waning Crescent",
            "name_bn": "কৃষ্ণপক্ষ ক্রিসেন্ট",
            "illumination": f"{illumination:.0f}%"
        }
