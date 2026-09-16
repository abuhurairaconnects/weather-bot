"""
Agriculture Mode Weather Advisory Service
Provides actionable farming, irrigation, spraying, and crop-care advice tailored for farmers.
Formatted with clear bullet points and spacious sections for effortless reading.
"""
from typing import Dict, Any

def get_agriculture_advice(weather_data: Dict[str, Any], city_name: str, lang: str = "bn") -> str:
    """Generate clean, bulleted agricultural weather bulletin."""
    cur = weather_data.get("current", {})
    daily = weather_data.get("daily", {})
    
    temp = cur.get("temp", 26.0)
    humidity = cur.get("humidity", 60)
    wind_speed = cur.get("wind_speed", 10.0)
    rain_prob = cur.get("today_rain_chance_max", 0)
    rainfall_amount = cur.get("rainfall_amount", 0.0)
    
    precip_sums = daily.get("precipitation_sum", [0.0])
    next_3d_rain = sum(precip_sums[:3]) if len(precip_sums) >= 3 else rainfall_amount

    # 1. Irrigation Advice
    if next_3d_rain > 12.0 or rain_prob > 50:
        irrig_bullets_bn = [
            f"সেচ দেওয়া স্থগিত রাখুন (আগামী ২৪-৭২ ঘণ্টায় প্রায় {next_3d_rain:.1f} মিমি বৃষ্টি হতে পারে)।",
            "জমিতে অতিরিক্ত পানি জমে ফসল নষ্ট হওয়া রোধে নিষ্কাশন নালা পরিষ্কার রাখুন।"
        ]
        irrig_bullets_en = [
            f"Hold irrigation (approx {next_3d_rain:.1f} mm rain expected over next 24-72 hours).",
            "Keep drainage channels clear to prevent waterlogging."
        ]
    elif humidity < 50 and temp > 30:
        irrig_bullets_bn = [
            "তাপমাত্রা বেশি এবং বাতাস শুষ্ক থাকায় জমিতে সেচ দেওয়া প্রয়োজন।",
            "বাষ্পীভবন কমাতে সকাল বা শেষ বিকেলে সেচ দেওয়া সবচেয়ে ভালো।"
        ]
        irrig_bullets_en = [
            "Irrigation recommended due to high evaporation rates.",
            "Water in early morning or late afternoon to maximize absorption."
        ]
    else:
        irrig_bullets_bn = [
            "মাটিতে পরিমিত আর্দ্রতা রয়েছে।",
            "মাটির অবস্থা দেখে প্রয়োজন অনুযায়ী হালকা সেচ দিন।"
        ]
        irrig_bullets_en = [
            "Soil moisture is at moderate levels.",
            "Apply light irrigation only if topsoil feels dry."
        ]

    # 2. Pesticide / Fertilizer Spraying Advice
    if wind_speed > 16.0:
        spray_bullets_bn = [
            f"বাতাসের বেগ বেশি ({wind_speed:.1f} কিমি/ঘণ্টা), তাই স্প্রে করা স্থগিত রাখুন।",
            "বাতাস শান্ত হলে ওষুধ প্রয়োগ করুন, যাতে ছড়িয়ে নষ্ট না হয়।"
        ]
        spray_bullets_en = [
            f"Avoid spraying due to strong winds ({wind_speed:.1f} km/h).",
            "Wait for calmer conditions to avoid chemical drift."
        ]
    elif rain_prob > 40:
        spray_bullets_bn = [
            "বৃষ্টির সম্ভাবনা থাকায় সার বা কীটনাশক স্প্রে করবেন না।",
            "বৃষ্টিতে স্প্রে করা রাসায়নিক ধুয়ে গিয়ে কার্যকারিতা নষ্ট হতে পারে।"
        ]
        spray_bullets_en = [
            "Delay spraying; rain is likely.",
            "Precipitation will wash away applied agrochemicals."
        ]
    else:
        spray_bullets_bn = [
            "বাতাস শান্ত ও অনুকূল, বালাইনাশক ও সার স্প্রে করার উপযুক্ত সময়।",
            "সকালের দিকে স্প্রে করলে ভালো ফল পাওয়া যাবে।"
        ]
        spray_bullets_en = [
            "Favorable calm weather for pesticide/fertilizer application.",
            "Morning hours are ideal for treatment."
        ]

    # 3. Post-Harvest / Crop Drying
    if rain_prob < 25 and humidity < 70 and temp >= 24:
        dry_bullets_bn = [
            "রোদ ও শুষ্ক আবহাওয়া ধান, ভুট্টা বা বীজ শুকানোর জন্য দারুণ উপযোগী।"
        ]
        dry_bullets_en = [
            "Optimal sunshine for drying grain, paddy, and seeds."
        ]
    else:
        dry_bullets_bn = [
            "বাতাসে আর্দ্রতা বেশি বা বৃষ্টির ঝুঁকি থাকায় রোদে শুকানো ঝুঁকিপূর্ণ।",
            "হঠাৎ বৃষ্টি থেকে ফসল বাঁচাতে ত্রিপল বা পলিথিন প্রস্তুত রাখুন।"
        ]
        dry_bullets_en = [
            "High moisture and damp air; sun-drying requires caution.",
            "Keep tarpaulins handy in case of sudden rain."
        ]

    # 4. Temperature / Pest Alerts
    alerts_bn = []
    alerts_en = []
    if temp > 35:
        alerts_bn.append("তীব্র তাপপ্রবাহে চারাগাছের গোড়ায় খড় দিয়ে মালচিং করুন।")
        alerts_en.append("Use organic mulching to shield seedling roots from extreme heat.")
    elif temp < 13:
        alerts_bn.append("শৈত্যপ্রবাহ ও কুয়াশায় ধানের বীজতলা রাতে পলিথিন দিয়ে ঢেকে রাখুন।")
        alerts_en.append("Cover seedbeds with plastic sheets overnight against cold snaps.")
    if humidity > 85:
        alerts_bn.append("অতিরিক্ত আর্দ্রতায় ছত্রাক ও ব্লাস্ট রোগের ঝুঁকি রয়েছে। নিয়মিত ক্ষেত পর্যবেক্ষণ করুন।")
        alerts_en.append("High humidity promotes fungal blast diseases. Inspect fields regularly.")
    if not alerts_bn:
        alerts_bn.append("বর্তমানে আবহাওয়া শান্ত রয়েছে, বড় কোনো আপৎকালীন ঝুঁকি নেই।")
        alerts_en.append("Calm agricultural conditions with no immediate hazards.")

    if lang == "bn":
        irrig_str = "\n".join([f"• {b}" for b in irrig_bullets_bn])
        spray_str = "\n".join([f"• {b}" for b in spray_bullets_bn])
        dry_str = "\n".join([f"• {b}" for b in dry_bullets_bn])
        alerts_str = "\n".join([f"• {b}" for b in alerts_bn])

        return (
            f"🌾 **কৃষি আবহাওয়া বুলেটিন — {city_name}**\n"
            f"──────────────────────\n\n"
            f"📊 **মাঠের অবস্থা:**\n"
            f"• তাপমাত্রা: {temp:.1f}°C (আর্দ্রতা: {humidity}%)\n"
            f"• বাতাসের গতি: {wind_speed:.1f} কিমি/ঘণ্টা\n"
            f"• বৃষ্টির সম্ভাবনা: {rain_prob}% (৩ দিনে মোট: {next_3d_rain:.1f} মিমি)\n\n"
            f"💧 **সেচ সংক্রান্ত পরামর্শ:**\n"
            f"{irrig_str}\n\n"
            f"🌱 **কীটনাশক ও সার প্রয়োগ:**\n"
            f"{spray_str}\n\n"
            f"☀️ **ফসল ও বীজ শুকানো:**\n"
            f"{dry_str}\n\n"
            f"⚠️ **রোগবালাই ও সুরক্ষা বার্তা:**\n"
            f"{alerts_str}\n\n"
            f"──────────────────────\n"
            f"👨‍🌾 *মাঠপর্যায়ে আবহাওয়ার তথ্য মেনে ফসল সুরক্ষিত রাখুন।*"
        )
    else:
        irrig_str = "\n".join([f"• {b}" for b in irrig_bullets_en])
        spray_str = "\n".join([f"• {b}" for b in spray_bullets_en])
        dry_str = "\n".join([f"• {b}" for b in dry_bullets_en])
        alerts_str = "\n".join([f"• {b}" for b in alerts_en])

        return (
            f"🌾 **Agricultural Advisory — {city_name}**\n"
            f"──────────────────────\n\n"
            f"📊 **Field Conditions:**\n"
            f"• Temperature: {temp:.1f}°C (Humidity: {humidity}%)\n"
            f"• Wind Speed: {wind_speed:.1f} km/h\n"
            f"• Rain Chance: {rain_prob}% (3-Day Total: {next_3d_rain:.1f} mm)\n\n"
            f"💧 **Irrigation Advice:**\n"
            f"{irrig_str}\n\n"
            f"🌱 **Fertilizer & Spraying:**\n"
            f"{spray_str}\n\n"
            f"☀️ **Post-Harvest Drying:**\n"
            f"{dry_str}\n\n"
            f"⚠️ **Crop Health & Disease Alert:**\n"
            f"{alerts_str}\n\n"
            f"──────────────────────\n"
            f"👨‍🌾 *Leverage agro-weather insights to safeguard your yield.*"
        )
