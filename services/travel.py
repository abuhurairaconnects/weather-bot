"""
Travel Weather Planner & Route Advisory Service
Compares origin and destination conditions and provides tailored packing and journey advice.
Formatted with clean bullet points and spacious sections.
"""
from typing import Dict, Any, Optional
from services.weather_api import search_city, get_weather_data
from utils.i18n import get_wmo_description

async def plan_travel(origin_name: str, dest_name: str, lang: str = "bn") -> Optional[str]:
    """Compare origin and destination weather and formulate clean bulleted travel advisory."""
    origin_results = await search_city(origin_name)
    dest_results = await search_city(dest_name)

    if not origin_results or not dest_results:
        return None

    orig = origin_results[0]
    dest = dest_results[0]

    orig_weather = await get_weather_data(orig["lat"], orig["lon"])
    dest_weather = await get_weather_data(dest["lat"], dest["lon"])

    if not orig_weather or not dest_weather:
        return None

    o_cur = orig_weather["current"]
    d_cur = dest_weather["current"]

    o_cond, o_emoji = get_wmo_description(o_cur["wmo_code"], lang)
    d_cond, d_emoji = get_wmo_description(d_cur["wmo_code"], lang)

    o_temp = o_cur["temp"]
    d_temp = d_cur["temp"]
    temp_diff = d_temp - o_temp

    d_rain_prob = d_cur.get("today_rain_chance_max", 0)
    d_wind = d_cur.get("wind_speed", 10.0)
    d_uv = d_cur.get("today_max_uv", 0.0)

    # Packing suggestions
    packing = []
    if d_rain_prob >= 35 or d_cur.get("rainfall_amount", 0.0) > 0.5:
        packing.append("ছাতা বা রেইনকোট" if lang == "bn" else "Umbrella or raincoat")
    if d_temp < 18:
        packing.append("হালকা জ্যাকেট বা শাল" if lang == "bn" else "Light jacket or shawl")
    elif d_temp < 12:
        packing.append("ভারী শীতের গরম পোশাক" if lang == "bn" else "Warm thermal layers")
    else:
        packing.append("হালকা সুতি ও আরামদায়ক কাপড়" if lang == "bn" else "Light cotton clothing")
    if d_uv >= 5:
        packing.append("সানগ্লাস ও সানস্ক্রিন (SPF 30+)" if lang == "bn" else "Sunglasses & Sunscreen")
    if d_cur.get("visibility_km", 10.0) < 3.0:
        packing.append("গাড়ির কুয়াশা বা ফগ লাইট" if lang == "bn" else "Fog lights for vehicle")

    packing_bullets = "\n".join([f"• {item}" for item in packing])

    # Temperature difference summary
    if abs(temp_diff) < 1.5:
        diff_summary = "উভয় স্থানের তাপমাত্রা প্রায় কাছাকাছি।" if lang == "bn" else "Both locations have similar temperatures."
    elif temp_diff > 0:
        diff_summary = f"গন্তব্যের তাপমাত্রা {abs(temp_diff):.1f}°C বেশি (তুলনামূলক গরম)।" if lang == "bn" else f"Destination is {abs(temp_diff):.1f}°C warmer."
    else:
        diff_summary = f"গন্তব্যের তাপমাত্রা {abs(temp_diff):.1f}°C কম (তুলনামূলক শীতল)।" if lang == "bn" else f"Destination is {abs(temp_diff):.1f}°C cooler."

    # Road trip warnings
    hazard_notes = []
    if d_rain_prob > 60:
        hazard_notes.append("গন্তব্যে ভারী বৃষ্টির সম্ভাবনা রয়েছে" if lang == "bn" else "Heavy rain anticipated at destination")
    if d_wind > 35:
        hazard_notes.append("তীব্র বাতাস বা ঝড়ের শঙ্কা" if lang == "bn" else "Strong wind/storm advisory")

    hazard_str = "\n".join([f"• ⚠️ {h}" for h in hazard_notes]) if hazard_notes else ("• ✅ যাত্রাপথে বড় কোনো বৈরী আবহাওয়া নেই" if lang == "bn" else "• ✅ Clear route conditions")

    if lang == "bn":
        return (
            f"🧳 **ভ্রমণ আবহাওয়া ও রোড-ট্রিপ প্ল্যানার**\n"
            f"──────────────────────\n"
            f"📍 **রুট:** {orig['name']} ➡️ {dest['name']}\n\n"
            f"🚩 **যাত্রার স্থান ({orig['name']}):**\n"
            f"• আকাশ: {o_emoji} {o_cond}\n"
            f"• তাপমাত্রা: {o_temp:.1f}°C (আর্দ্রতা: {o_cur['humidity']}%)\n\n"
            f"🎯 **গন্তব্য ({dest['name']}):**\n"
            f"• আকাশ: {d_emoji} {d_cond}\n"
            f"• তাপমাত্রা: {d_temp:.1f}°C | বৃষ্টি: {d_rain_prob}%\n"
            f"• বাতাস: {d_wind:.1f} কিমি/ঘ | UV: {d_uv:.1f}\n\n"
            f"🌡️ **তাপমাত্রার তুলনা:**\n"
            f"• {diff_summary}\n\n"
            f"🛣️ **সতর্কতা ও রোড কন্ডিশন:**\n"
            f"{hazard_str}\n\n"
            f"🎒 **প্যাকিং তালিকা:**\n"
            f"{packing_bullets}\n\n"
            f"──────────────────────\n"
            f"✈️ *আপনার যাত্রা নিরাপদ ও আনন্দময় হোক!*"
        )
    else:
        return (
            f"🧳 **Travel Weather & Route Advisory**\n"
            f"──────────────────────\n"
            f"📍 **Route:** {orig['name']} ➡️ {dest['name']}\n\n"
            f"🚩 **Origin ({orig['name']}):**\n"
            f"• Sky: {o_emoji} {o_cond}\n"
            f"• Temperature: {o_temp:.1f}°C (Humidity: {o_cur['humidity']}%)\n\n"
            f"🎯 **Destination ({dest['name']}):**\n"
            f"• Sky: {d_emoji} {d_cond}\n"
            f"• Temperature: {d_temp:.1f}°C | Rain: {d_rain_prob}%\n"
            f"• Wind: {d_wind:.1f} km/h | UV: {d_uv:.1f}\n\n"
            f"🌡️ **Temperature Comparison:**\n"
            f"• {diff_summary}\n\n"
            f"🛣️ **Hazards & Road Conditions:**\n"
            f"{hazard_str}\n\n"
            f"🎒 **Recommended Packing List:**\n"
            f"{packing_bullets}\n\n"
            f"──────────────────────\n"
            f"✈️ *Wishing you a safe and pleasant journey!*"
        )
