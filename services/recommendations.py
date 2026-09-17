"""
Smart AI/Rule-based Weather Recommendation Engine
Generates context-aware practical advice for daily life, clothing, sports, and outdoor activities.
Organized with clean spacing and bullet points for effortless readability.
"""
from typing import Dict, Any

def generate_recommendations(weather_data: Dict[str, Any], lang: str = "bn") -> Dict[str, Any]:
    """Analyzes current and forecast weather data to produce actionable recommendations."""
    cur = weather_data.get("current", {})
    temp = cur.get("temp", 25.0)
    feels_like = cur.get("feels_like", temp)
    humidity = cur.get("humidity", 50)
    rain_prob = cur.get("today_rain_chance_max", 0)
    rainfall = cur.get("rainfall_amount", 0.0)
    wmo_code = cur.get("wmo_code", 0)
    wind_speed = cur.get("wind_speed", 10.0)
    uv = cur.get("today_max_uv", cur.get("uv_index", 0.0))
    aqi = cur.get("aqi", {}).get("us_aqi", 50)
    visibility = cur.get("visibility_km", 10.0)

    # 1. Umbrella
    is_rainy = wmo_code in [51, 53, 55, 61, 63, 65, 80, 81, 82, 95, 96, 99] or rainfall > 0.2 or rain_prob >= 40
    if is_rainy:
        umbrella_bn = f"বৃষ্টির সম্ভাবনা বেশি ({rain_prob}%)। বাইরে বের হলে অবশ্যই সাথে ছাতা রাখুন।"
        umbrella_en = f"High chance of rain ({rain_prob}%). Make sure to carry an umbrella."
    else:
        umbrella_bn = "বৃষ্টির সম্ভাবনা বেশ কম। ছাতা নেওয়ার প্রয়োজন নেই।"
        umbrella_en = "Low chance of rain. No umbrella needed."

    # 2. Clothing
    if feels_like < 12:
        clothing_bn = "বেশ ঠান্ডা অনুভূত হচ্ছে। ভারী জ্যাকেট বা গরম পোশাক পরিধান করুন।"
        clothing_en = "Very cold outside. Wear a heavy jacket or thermal layers."
    elif feels_like < 20:
        clothing_bn = "হালকা শীতল বাতাস রয়েছে। ফুলহাতা জামা বা পাতলা জ্যাকেট আরামদায়ক হবে।"
        clothing_en = "Mild cool breeze. A light jacket or long sleeves will be comfortable."
    elif feels_like > 34:
        clothing_bn = "প্রচণ্ড গরম ও আর্দ্রতা। ঢিলেঢালা সুতি কাপড় পরুন ও বেশি পানি পান করুন।"
        clothing_en = "Hot and humid. Wear light breathable cotton clothes and drink plenty of water."
    else:
        clothing_bn = "আবহাওয়া আরামদায়ক। স্বাভাবিক ক্যাজুয়াল পোশাকের জন্য উপযুক্ত।"
        clothing_en = "Comfortable temperature. Normal casual attire is great."

    # 3. Sun Protection
    if uv >= 6:
        sun_bn = f"সূর্যের তেজ ও UV সূচক বেশি ({uv:.1f})। রোদ থেকে বাঁচতে সানগ্লাস ও সানস্ক্রিন ব্যবহার করুন।"
        sun_en = f"High UV index ({uv:.1f}). Apply sunscreen (SPF 30+) and wear sunglasses."
    elif uv >= 3:
        sun_bn = f"মাঝারি রোদ (UV {uv:.1f})। প্রয়োজনে সানগ্লাস বা টুপি ব্যবহার করতে পারেন।"
        sun_en = f"Moderate sunshine (UV {uv:.1f}). Sunglasses or a hat are recommended."
    else:
        sun_bn = "সূর্যের অতিবেগুনি রশ্মি কম। অতিরিক্ত সানস্ক্রিনের প্রয়োজন নেই।"
        sun_en = "Low UV radiation. No special sun protection required."

    # 4. Driving
    driving_warnings = []
    if visibility < 2.0:
        driving_warnings.append("কুয়াশা বা বৃষ্টির কারণে দৃষ্টিসীমা কম" if lang == "bn" else "low visibility")
    if is_rainy:
        driving_warnings.append("রাস্তা ভেজা ও পিচ্ছিল" if lang == "bn" else "slippery wet roads")
    if wind_speed > 35:
        driving_warnings.append("তীব্র বাতাস" if lang == "bn" else "strong winds")

    if driving_warnings:
        driving_bn = f"সতর্কতা: {', '.join(driving_warnings)}। নিরাপদ গতি বজায় রাখুন।"
        driving_en = f"Caution: {', '.join(driving_warnings)}. Maintain a safe speed."
    else:
        driving_bn = "রাস্তা পরিষ্কার ও আবহাওয়া স্বাভাবিক। ড্রাইভিংয়ের জন্য নিরাপদ।"
        driving_en = "Roads are clear and weather is calm. Safe for driving."

    # 5. Outdoors & Exercise
    if aqi > 150:
        outdoor_bn = f"বাতাসের দূষণ মাত্রা বেশি (AQI: {aqi})। বাইরে ভারী ব্যায়াম পরিহার করুন।"
        outdoor_en = f"Air pollution is unhealthy (AQI: {aqi}). Avoid intense outdoor workouts."
    elif is_rainy or feels_like > 36 or feels_like < 10:
        outdoor_bn = "প্রতিকূল আবহাওয়া। বাইরে দীর্ঘ সময় কাটানো এড়িয়ে চলা ভালো।"
        outdoor_en = "Unfavorable weather. Limit prolonged outdoor exposure."
    else:
        outdoor_bn = "আবহাওয়া খুবই চমৎকার। বাইরে হাঁটা, জগিং বা খেলাধুলার জন্য উপযুক্ত সময়।"
        outdoor_en = "Pleasant conditions. Great time for walking, jogging, or sports."

    # 6. Clothes Drying
    if not is_rainy and humidity < 72 and rain_prob < 30:
        drying_bn = "বাতাসে আর্দ্রতা কম ও রোদ আছে। কাপড় দ্রুত শুকাবে।"
        drying_en = "Low moisture and ample sun. Good conditions for drying clothes."
    else:
        drying_bn = "বাতাসে আর্দ্রতা বেশি বা বৃষ্টির ঝুঁকি রয়েছে। ঘরের ভেতরে শুকানো ভালো।"
        drying_en = "High humidity or rain risk. Drying indoors is recommended."

    # 7. Photography
    if not is_rainy and visibility >= 8.0 and wmo_code in [0, 1, 2]:
        photo_bn = "পরিষ্কার আকাশ ও ভালো আলো। আউটডোর ল্যান্ডস্কেপ ফটোগ্রাফির জন্য দারুণ।"
        photo_en = "Clear skies and good visibility. Excellent for outdoor photography."
    else:
        photo_bn = "আকাশ মেঘলা। নরম ও ডিফিউজড লাইটের ছবি তোলার উপযুক্ত।"
        photo_en = "Overcast lighting. Suitable for diffused, soft-light photography."

    return {
        "umbrella": umbrella_bn if lang == "bn" else umbrella_en,
        "clothing": clothing_bn if lang == "bn" else clothing_en,
        "sun_protection": sun_bn if lang == "bn" else sun_en,
        "driving": driving_bn if lang == "bn" else driving_en,
        "outdoor": outdoor_bn if lang == "bn" else outdoor_en,
        "drying": drying_bn if lang == "bn" else drying_en,
        "photography": photo_bn if lang == "bn" else photo_en
    }

def format_recommendations_message(rec: Dict[str, Any], city_name: str, lang: str = "bn") -> str:
    """Format smart recommendations into clean, bulleted, and spacious Telegram text."""
    if lang == "bn":
        return (
            "👋 **আসসালামু আলাইকুম, আমি আবু হুরাইরার AI অ্যাসিস্ট্যান্ট, আপনাকে কীভাবে সাহায্য করি?**\n\n"
            f"🧠 **স্মার্ট আবহাওয়া পরামর্শ — {city_name}**\n"
            f"──────────────────────\n\n"
            f"☂️ **ছাতা ব্যবহার:**\n"
            f"• {rec['umbrella']}\n\n"
            f"👕 **পোশাকের পরামর্শ:**\n"
            f"• {rec['clothing']}\n\n"
            f"☀️ **রোদ ও ত্বক সুরক্ষা:**\n"
            f"• {rec['sun_protection']}\n\n"
            f"🚗 **ড্রাইভিং সতর্কতা:**\n"
            f"• {rec['driving']}\n\n"
            f"🏃 **আউটডোর ও ব্যায়াম:**\n"
            f"• {rec['outdoor']}\n\n"
            f"🧺 **কাপড় শুকানো:**\n"
            f"• {rec['drying']}\n\n"
            f"📸 **ফটোগ্রাফি:**\n"
            f"• {rec['photography']}\n\n"
            f"──────────────────────\n"
            f"💡 *আবহাওয়া পরিবর্তনের সাথে পরামর্শগুলো আপডেট হয়।*"
        )
    else:
        return (
            "👋 **Assalamu Alaikum, I am Abu Huraira's AI Assistant, how can I help you?**\n\n"
            f"🧠 **Smart Weather Advice — {city_name}**\n"
            f"──────────────────────\n\n"
            f"☂️ **Umbrella Guidance:**\n"
            f"• {rec['umbrella']}\n\n"
            f"👕 **Clothing Advice:**\n"
            f"• {rec['clothing']}\n\n"
            f"☀️ **Sun Protection:**\n"
            f"• {rec['sun_protection']}\n\n"
            f"🚗 **Driving Conditions:**\n"
            f"• {rec['driving']}\n\n"
            f"🏃 **Outdoors & Fitness:**\n"
            f"• {rec['outdoor']}\n\n"
            f"🧺 **Clothes Drying:**\n"
            f"• {rec['drying']}\n\n"
            f"📸 **Photography:**\n"
            f"• {rec['photography']}\n\n"
            f"──────────────────────\n"
            f"💡 *Recommendations dynamically adapt based on real-time data.*"
        )
