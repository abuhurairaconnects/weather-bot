"""
Forecast Handlers: /forecast, /hourly, /rain, /airquality.
Provides extended daily forecasts, 24-hour hourly breakdowns, and in-depth pollution analysis.
"""
from telegram import Update
from telegram.ext import ContextTypes
from database.db import get_or_create_user, log_search
from services.weather_api import search_city, get_weather_data, format_temp
from utils.i18n import get_wmo_description, get_aqi_category

def format_daily_forecast_message(weather_data: dict, city_name: str, lang: str = "bn", unit: str = "C") -> str:
    """Format 7-10 day daily forecast bulletin."""
    daily = weather_data.get("daily", {})
    times = daily.get("time", [])[:7]  # 7-day overview
    wmo_codes = daily.get("weather_code", [])
    max_temps = daily.get("temperature_2m_max", [])
    min_temps = daily.get("temperature_2m_min", [])
    rain_probs = daily.get("precipitation_probability_max", [])
    precip_sums = daily.get("precipitation_sum", [])
    uv_max = daily.get("uv_index_max", [])

    lines = []
    if lang == "bn":
        lines.append(f"📅 **৭ দিনের আবহাওয়ার পূর্বাভাস — {city_name}**")
        lines.append("──────────────────────\n")
        for i in range(len(times)):
            date_str = times[i]  # YYYY-MM-DD
            wmo = wmo_codes[i] if i < len(wmo_codes) else 0
            cond_text, emoji = get_wmo_description(wmo, lang)
            max_t = format_temp(max_temps[i] if i < len(max_temps) else 0, unit)
            min_t = format_temp(min_temps[i] if i < len(min_temps) else 0, unit)
            rain_p = rain_probs[i] if i < len(rain_probs) else 0
            precip = precip_sums[i] if i < len(precip_sums) else 0.0
            uv = uv_max[i] if i < len(uv_max) else 0.0

            lines.append(
                f"🗓️ **{date_str}:** {emoji} {cond_text}\n"
                f"• তাপমাত্রা: {min_t} থেকে {max_t}\n"
                f"• বৃষ্টিপাত: {rain_p}% ({precip:.1f} মিমি) | UV: {uv:.1f}\n"
            )
        lines.append("──────────────────────")
        lines.append("💡 *প্রতিদিনের সম্ভাব্য তাপমাত্রা সীমা ও বৃষ্টির পূর্বাভাস।*")
    else:
        lines.append(f"📅 **7-Day Weather Forecast — {city_name}**")
        lines.append("──────────────────────\n")
        for i in range(len(times)):
            date_str = times[i]
            wmo = wmo_codes[i] if i < len(wmo_codes) else 0
            cond_text, emoji = get_wmo_description(wmo, lang)
            max_t = format_temp(max_temps[i] if i < len(max_temps) else 0, unit)
            min_t = format_temp(min_temps[i] if i < len(min_temps) else 0, unit)
            rain_p = rain_probs[i] if i < len(rain_probs) else 0
            precip = precip_sums[i] if i < len(precip_sums) else 0.0
            uv = uv_max[i] if i < len(uv_max) else 0.0

            lines.append(
                f"🗓️ **{date_str}:** {emoji} {cond_text}\n"
                f"• Temp: {min_t} to {max_t}\n"
                f"• Rain: {rain_p}% ({precip:.1f} mm) | UV: {uv:.1f}\n"
            )
        lines.append("──────────────────────")
        lines.append("💡 *Expected temperature range and precipitation estimate.*")

    return "\n".join(lines)

def format_hourly_message(weather_data: dict, city_name: str, lang: str = "bn", unit: str = "C") -> str:
    """Format next 24 hours in 3-hour intervals with clean bullets."""
    hourly = weather_data.get("hourly", {})
    times = hourly.get("time", [])[:24]
    temps = hourly.get("temperature_2m", [])[:24]
    wmo_codes = hourly.get("weather_code", [])[:24]
    rain_probs = hourly.get("precipitation_probability", [])[:24]
    winds = hourly.get("wind_speed_10m", [])[:24]

    lines = []
    if lang == "bn":
        lines.append(f"📆 **২৪ ঘণ্টার প্রতি ঘণ্টার পূর্বাভাস — {city_name}**")
        lines.append("──────────────────────\n")
        for i in range(0, len(times), 3):
            t_str = times[i].split("T")[1][:5]
            temp = format_temp(temps[i], unit)
            wmo = wmo_codes[i]
            _, emoji = get_wmo_description(wmo, lang)
            r_prob = rain_probs[i]
            w_spd = winds[i]
            lines.append(f"• **{t_str}** ➡️ {emoji} **{temp}** | 🌧️ {r_prob}% বৃষ্টি | 💨 {w_spd:.0f} কিমি/ঘ")
        lines.append("\n──────────────────────")
        lines.append("📊 চার্ট দেখতে /charts কমান্ড ব্যবহার করুন।")
    else:
        lines.append(f"📆 **24-Hour Forecast (Every 3h) — {city_name}**")
        lines.append("──────────────────────\n")
        for i in range(0, len(times), 3):
            t_str = times[i].split("T")[1][:5]
            temp = format_temp(temps[i], unit)
            wmo = wmo_codes[i]
            _, emoji = get_wmo_description(wmo, lang)
            r_prob = rain_probs[i]
            w_spd = winds[i]
            lines.append(f"• **{t_str}** ➡️ {emoji} **{temp}** | 🌧️ {r_prob}% rain | 💨 {w_spd:.0f} km/h")
        lines.append("\n──────────────────────")
        lines.append("📊 Use /charts to view graphical visualization.")

    return "\n".join(lines)

def format_air_quality_message(weather_data: dict, city_name: str, lang: str = "bn") -> str:
    """Format Air Quality Index and pollutant breakdown cleanly."""
    aqi_data = weather_data.get("current", {}).get("aqi", {})
    us_aqi = aqi_data.get("us_aqi", 0)
    pm25 = aqi_data.get("pm2_5", 0.0)
    pm10 = aqi_data.get("pm10", 0.0)
    co = aqi_data.get("co", 0.0)
    no2 = aqi_data.get("no2", 0.0)
    so2 = aqi_data.get("so2", 0.0)
    o3 = aqi_data.get("o3", 0.0)

    category, emoji, advice = get_aqi_category(us_aqi, lang)

    if lang == "bn":
        return (
            f"🌫️ **বায়ুমান ও দূষণ সূচক (AQI) — {city_name}**\n"
            f"──────────────────────\n\n"
            f"📊 **সামগ্রিক স্কোর:** {us_aqi} ({category} {emoji})\n\n"
            f"🧪 **প্রধান দূষণকারী উপাদানসমূহ:**\n"
            f"• PM2.5 (অতি সূক্ষ্ম ধূলিকণা): {pm25:.1f} µg/m³\n"
            f"• PM10 (শ্বাসনালীর ধূলিকণা): {pm10:.1f} µg/m³\n"
            f"• CO (কার্বন মনোক্সাইড): {co:.1f} µg/m³\n"
            f"• NO₂ (নাইট্রোজেন ডাইঅক্সাইড): {no2:.1f} µg/m³\n"
            f"• SO₂ (সালফার ডাইঅক্সাইড): {so2:.1f} µg/m³\n"
            f"• O₃ (ওজোন): {o3:.1f} µg/m³\n\n"
            f"🏥 **স্বাস্থ্য সতর্কতা ও পরামর্শ:**\n"
            f"• {advice}\n\n"
            f"──────────────────────\n"
            f"💡 *AQI ১০০ ছাড়িয়ে গেলে বাইরে চলাচলে মাস্ক ব্যবহার করুন।*"
        )
    else:
        return (
            f"🌫️ **Air Quality Report (AQI) — {city_name}**\n"
            f"──────────────────────\n\n"
            f"📊 **Overall Score:** {us_aqi} ({category} {emoji})\n\n"
            f"🧪 **Pollutant Concentrations:**\n"
            f"• PM2.5 (Fine particulate matter): {pm25:.1f} µg/m³\n"
            f"• PM10 (Coarse particulate matter): {pm10:.1f} µg/m³\n"
            f"• CO (Carbon Monoxide): {co:.1f} µg/m³\n"
            f"• NO₂ (Nitrogen Dioxide): {no2:.1f} µg/m³\n"
            f"• SO₂ (Sulfur Dioxide): {so2:.1f} µg/m³\n"
            f"• O₃ (Ozone): {o3:.1f} µg/m³\n\n"
            f"🏥 **Health Advisory:**\n"
            f"• {advice}\n\n"
            f"──────────────────────\n"
            f"💡 *Wear a protective mask outdoors when AQI exceeds 100.*"
        )

async def forecast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /forecast [city]."""
    user = update.effective_user
    db_user = await get_or_create_user(user.id, user.username, user.first_name)
    lang = db_user.get("language", "bn")
    unit = db_user.get("temp_unit", "C")

    args = context.args
    query = " ".join(args).strip() if args else (db_user.get("default_city") or "Dhaka")

    cities = await search_city(query)
    if not cities:
        await update.message.reply_text(f"❌ '{query}' শহর পাওয়া যায়নি।" if lang == "bn" else f"❌ City '{query}' not found.")
        return

    city = cities[0]
    await log_search(user.id, city["name"])
    data = await get_weather_data(city["lat"], city["lon"], unit)
    if not data:
        await update.message.reply_text("⚠️ পূর্বাভাস লোড করা যায়নি।")
        return

    msg = format_daily_forecast_message(data, city["display_name"], lang, unit)
    await update.message.reply_text(msg, parse_mode="Markdown")

async def hourly_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /hourly [city]."""
    user = update.effective_user
    db_user = await get_or_create_user(user.id, user.username, user.first_name)
    lang = db_user.get("language", "bn")
    unit = db_user.get("temp_unit", "C")

    args = context.args
    query = " ".join(args).strip() if args else (db_user.get("default_city") or "Dhaka")

    cities = await search_city(query)
    if not cities:
        await update.message.reply_text(f"❌ '{query}' শহর পাওয়া যায়নি।" if lang == "bn" else f"❌ City '{query}' not found.")
        return

    city = cities[0]
    await log_search(user.id, city["name"])
    data = await get_weather_data(city["lat"], city["lon"], unit)
    if not data:
        await update.message.reply_text("⚠️ পূর্বাভাস লোড করা যায়নি।")
        return

    msg = format_hourly_message(data, city["display_name"], lang, unit)
    await update.message.reply_text(msg, parse_mode="Markdown")

async def airquality_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /airquality [city]."""
    user = update.effective_user
    db_user = await get_or_create_user(user.id, user.username, user.first_name)
    lang = db_user.get("language", "bn")
    unit = db_user.get("temp_unit", "C")

    args = context.args
    query = " ".join(args).strip() if args else (db_user.get("default_city") or "Dhaka")

    cities = await search_city(query)
    if not cities:
        await update.message.reply_text(f"❌ '{query}' শহর পাওয়া যায়নি।" if lang == "bn" else f"❌ City '{query}' not found.")
        return

    city = cities[0]
    await log_search(user.id, city["name"])
    data = await get_weather_data(city["lat"], city["lon"], unit)
    if not data:
        await update.message.reply_text("⚠️ এয়ার কোয়ালিটি ডেটা লোড করা যায়নি।")
        return

    msg = format_air_quality_message(data, city["display_name"], lang)
    await update.message.reply_text(msg, parse_mode="Markdown")

async def rain_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /rain [city] (detailed rain analysis)."""
    user = update.effective_user
    db_user = await get_or_create_user(user.id, user.username, user.first_name)
    lang = db_user.get("language", "bn")
    unit = db_user.get("temp_unit", "C")

    args = context.args
    query = " ".join(args).strip() if args else (db_user.get("default_city") or "Dhaka")

    cities = await search_city(query)
    if not cities:
        await update.message.reply_text(f"❌ '{query}' শহর পাওয়া যায়নি।" if lang == "bn" else f"❌ City '{query}' not found.")
        return

    city = cities[0]
    data = await get_weather_data(city["lat"], city["lon"], unit)
    if not data:
        await update.message.reply_text("⚠️ ডেটা পাওয়া যায়নি।")
        return

    cur = data["current"]
    hourly = data.get("hourly", {})
    rain_probs = hourly.get("precipitation_probability", [])[:12]
    precips = hourly.get("precipitation", [])[:12]
    times = hourly.get("time", [])[:12]

    today_rain_chance = cur.get("today_rain_chance_max", 0)
    current_rainfall = cur.get("rainfall_amount", 0.0)

    # Next hours with rain
    rain_hours = []
    for i in range(len(times)):
        p = rain_probs[i] if i < len(rain_probs) else 0
        amt = precips[i] if i < len(precips) else 0.0
        t_label = times[i].split("T")[1][:5]
        if p >= 30 or amt > 0.1:
            rain_hours.append(f"• **{t_label}** 🌧️ {p}% সম্ভাবনা ({amt:.1f} মিমি)")

    rain_summary = "\n".join(rain_hours) if rain_hours else ("আগামী ১২ ঘণ্টার মধ্যে বৃষ্টির তেমন কোনো সম্ভাবনা নেই ☀️" if lang == "bn" else "No significant rain expected in the next 12 hours ☀️")

    if lang == "bn":
        msg = (
            f"🌧️ **বৃষ্টির বিস্তারিত আপডেট — {city['display_name']}**\n"
            f"──────────────────────\n\n"
            f"📊 **বৃষ্টিপাত সারসংক্ষেপ:**\n"
            f"• সর্বোচ্চ সম্ভাবনা: {today_rain_chance}%\n"
            f"• বর্তমান বৃষ্টিপাত: {current_rainfall:.1f} মিমি\n\n"
            f"⏰ **পরবর্তী ১২ ঘণ্টার পূর্বাভাস:**\n"
            f"{rain_summary}\n\n"
            f"☂️ **পরামর্শ:**\n"
            f"• {'বাইরে বের হলে অবশ্যই সাথে ছাতা রাখুন।' if today_rain_chance > 40 else 'বৃষ্টির সম্ভাবনা কম, ছাতা নেওয়ার প্রয়োজন নেই।'}\n\n"
            f"──────────────────────"
        )
    else:
        msg = (
            f"🌧️ **Rain & Precipitation Report — {city['display_name']}**\n"
            f"──────────────────────\n\n"
            f"📊 **Precipitation Summary:**\n"
            f"• Max Chance: {today_rain_chance}%\n"
            f"• Current Rain: {current_rainfall:.1f} mm\n\n"
            f"⏰ **Next 12 Hours Forecast:**\n"
            f"{rain_summary}\n\n"
            f"☂️ **Advice:**\n"
            f"• {'Make sure to carry an umbrella.' if today_rain_chance > 40 else 'Low chance of rain, no umbrella needed.'}\n\n"
            f"──────────────────────"
        )

    await update.message.reply_text(msg, parse_mode="Markdown")
