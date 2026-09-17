"""
Weather Handler: /weather, Location sharing, and Interactive Inline Button dispatcher.
Displays all 16+ basic weather metrics and links to smart sub-views.
"""
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database.db import get_or_create_user, log_search
from services.weather_api import search_city, get_weather_data, format_temp
from utils.i18n import get_wmo_description, get_wind_direction, get_aqi_category, get_uv_category
from services.recommendations import generate_recommendations, format_recommendations_message
from config import is_authorized, ACCESS_DENIED_MESSAGE_BN

def build_weather_buttons(lat: float, lon: float, city_name: str, lang: str = "bn") -> InlineKeyboardMarkup:
    """Build inline keyboard with core options: 24h, 7-Day, Smart Advice, Refresh."""
    c_clean = city_name.split(",")[0].strip()
    # Ensure byte length never exceeds Telegram's 64-byte callback_data limit
    c_short = c_clean.encode("utf-8")[:18].decode("utf-8", errors="ignore")
    if lang == "bn":
        keyboard = [
            [
                InlineKeyboardButton("📆 ২৪ ঘণ্টা", callback_data=f"hr:{lat:.4f}:{lon:.4f}:{c_short}"),
                InlineKeyboardButton("📅 ৭ দিন", callback_data=f"fc:{lat:.4f}:{lon:.4f}:{c_short}")
            ],
            [
                InlineKeyboardButton("🧠 স্মার্ট পরামর্শ", callback_data=f"adv:{lat:.4f}:{lon:.4f}:{c_short}"),
                InlineKeyboardButton("🔄 রিফ্রেশ", callback_data=f"ref:{lat:.4f}:{lon:.4f}:{c_short}")
            ]
        ]
    else:
        keyboard = [
            [
                InlineKeyboardButton("📆 24h Hourly", callback_data=f"hr:{lat:.4f}:{lon:.4f}:{c_short}"),
                InlineKeyboardButton("📅 7-Day", callback_data=f"fc:{lat:.4f}:{lon:.4f}:{c_short}")
            ],
            [
                InlineKeyboardButton("🧠 Smart Advice", callback_data=f"adv:{lat:.4f}:{lon:.4f}:{c_short}"),
                InlineKeyboardButton("🔄 Refresh", callback_data=f"ref:{lat:.4f}:{lon:.4f}:{c_short}")
            ]
        ]
    return InlineKeyboardMarkup(keyboard)

def get_severe_weather_alert(data: dict, lang: str = "bn") -> str:
    """Detect extreme or hazardous weather conditions and produce prominent safety alerts."""
    cur = data.get("current", {})
    hourly = data.get("hourly", {})
    wmo_code = cur.get("wmo_code", 0)
    wind_speed = cur.get("wind_speed", 0.0)
    temp = cur.get("temp", 25.0)
    rain_probs = hourly.get("precipitation_probability", [])
    
    # Check next 2-3 hours rain risk
    next_rain = max(rain_probs[:3]) if rain_probs else cur.get("today_rain_chance_max", 0)
    
    alerts = []
    if lang == "bn":
        if wmo_code in [95, 96, 99]:
            alerts.append("• ⚡ **বজ্রঝড় ও বজ্রপাত সতর্কতা:** আগামী কয়েক ঘণ্টায় তীব্র বজ্রপাত ও শিলাবৃষ্টির আশঙ্কা! খোলা মাঠ বা গাছের নিচে অবস্থান করবেন না, নিরাপদ পাকা আশ্রয়ে থাকুন।")
        elif next_rain >= 75:
            alerts.append(f"• 🌧️ **ভারী বৃষ্টিপাত সতর্কতা:** আগামী কয়েক ঘণ্টায় ভারি থেকে অতিভারি বর্ষণের প্রবল সম্ভাবনা ({next_rain}%)! নিম্নাঞ্চলে জলাবদ্ধতার বিষয়ে সতর্ক থাকুন।")
        
        if wind_speed >= 38.0:
            alerts.append(f"• 💨 **ঝড়ো হাওয়া সতর্কতা:** বাতাসের গতিবেগ ঘণ্টায় {wind_speed:.1f} কিমি ছাড়িয়েছে! দুর্বল স্থাপনা ও গাছপালা থেকে দূরে থাকুন।")
        
        if temp >= 38.0:
            alerts.append(f"• 🔥 **তীব্র তাপদাহ সতর্কতা:** তাপমাত্রা {temp:.1f}°C ছাড়িয়েছে! পর্যাপ্ত বিশুদ্ধ পানি পান করুন এবং সরাসরি তীব্র রোদ এড়িয়ে চলুন।")
        elif temp <= 10.0:
            alerts.append(f"• ❄️ **তীব্র শৈত্যপ্রবাহ সতর্কতা:** তাপমাত্রা {temp:.1f}°C-এ নেমেছে! শিশু ও বয়োবৃদ্ধদের পর্যাপ্ত গরম কাপড়ে রাখুন।")
    else:
        if wmo_code in [95, 96, 99]:
            alerts.append("• ⚡ **Severe Thunderstorm Alert:** High risk of lightning and hail in the coming hours! Stay indoors away from open fields and trees.")
        elif next_rain >= 75:
            alerts.append(f"• 🌧️ **Heavy Downpour Alert:** High probability of heavy rainfall ({next_rain}%)! Be cautious of urban waterlogging.")
        if wind_speed >= 38.0:
            alerts.append(f"• 💨 **Gale Wind Alert:** Wind speed exceeds {wind_speed:.1f} km/h! Stay safe from loose objects.")
        if temp >= 38.0:
            alerts.append(f"• 🔥 **Extreme Heatwave Alert:** Temp reached {temp:.1f}°C! Stay hydrated.")
        elif temp <= 10.0:
            alerts.append(f"• ❄️ **Severe Cold Wave Alert:** Temp dropped to {temp:.1f}°C! Wear warm layers.")

    if not alerts:
        return ""

    header = "⚠️ **জরুরি আবহাওয়া সতর্কতা:**" if lang == "bn" else "⚠️ **Severe Weather Warning:**"
    return f"{header}\n" + "\n".join(alerts) + "\n──────────────────────\n\n"

def format_current_weather_card(data: dict, city_name: str, lang: str = "bn", unit: str = "C") -> str:
    """Format full 16-parameter weather status card."""
    cur = data["current"]
    wmo_code = cur.get("wmo_code", 0)
    cond_text, cond_emoji = get_wmo_description(wmo_code, lang)
    severe_banner = get_severe_weather_alert(data, lang)
    
    temp_str = format_temp(cur.get("temp"), unit)
    feels_str = format_temp(cur.get("feels_like"), unit)
    dew_str = format_temp(cur.get("dew_point"), unit)
    max_t_str = format_temp(cur.get("today_max_temp"), unit)
    min_t_str = format_temp(cur.get("today_min_temp"), unit)

    humidity = cur.get("humidity", 0)
    wind_speed = cur.get("wind_speed", 0.0)
    wind_deg = cur.get("wind_direction_deg", 0.0)
    wind_dir = get_wind_direction(wind_deg, lang)
    
    rain_prob = cur.get("today_rain_chance_max", 0)
    rainfall = cur.get("rainfall_amount", 0.0)
    clouds = cur.get("cloud_cover", 0)
    visibility = cur.get("visibility_km", 10.0)
    pressure = cur.get("pressure", 1013)
    
    uv = cur.get("today_max_uv", 0.0)
    uv_cat, uv_emoji, _ = get_uv_category(uv, lang)

    aqi_val = cur.get("aqi", {}).get("us_aqi", 0)
    aqi_cat, aqi_emoji, _ = get_aqi_category(aqi_val, lang)

    moon = cur.get("moon", {})
    moon_name = moon.get("name_bn" if lang == "bn" else "name_en", "Moon")
    moon_emoji = moon.get("emoji", "🌕")
    moon_illum = moon.get("illumination", "50%")

    sunrise = cur.get("sunrise", "--:--")
    sunset = cur.get("sunset", "--:--")

    if lang == "bn":
        return (
            f"🌦️ **রিয়েল-টাইম আবহাওয়া পরিস্থিতি — {city_name}**\n"
            f"──────────────────────\n"
            f"{severe_banner}"
            f"🌡️ **তাপমাত্রা ও অনুভূতি:**\n"
            f"• বর্তমান তাপমাত্রা: **{temp_str}** (অনুভূত: {feels_str})\n"
            f"• আকাশের অবস্থা: {cond_emoji} {cond_text}\n"
            f"• আজকের সীমা: {min_t_str} থেকে {max_t_str}\n\n"
            f"💧 **আর্দ্রতা ও বাতাস:**\n"
            f"• আর্দ্রতা: {humidity}% | শিশিরাঙ্ক: {dew_str}\n"
            f"• বাতাসের বেগ: {wind_speed:.1f} কিমি/ঘণ্টা ({wind_dir})\n"
            f"• বায়ুচাপ: {pressure:.0f} hPa\n\n"
            f"🌧️ **বৃষ্টি ও আকাশ:**\n"
            f"• বৃষ্টির সম্ভাবনা: {rain_prob}% (বৃষ্টিপাত: {rainfall:.1f} মিমি)\n"
            f"• মেঘের আচ্ছাদন: {clouds}%\n"
            f"• দৃষ্টিসীমা: {visibility:.1f} কিমি\n\n"
            f"☀️ **সূর্য, চাঁদ ও পরিবেশ:**\n"
            f"• বায়ু দূষণ (AQI): {aqi_val} ({aqi_cat} {aqi_emoji})\n"
            f"• ইউভি সূচক: {uv:.1f} ({uv_cat} {uv_emoji})\n"
            f"• সূর্যোদয়: {sunrise} | সূর্যাস্ত: {sunset}\n"
            f"• চন্দ্রকলা: {moon_emoji} {moon_name} ({moon_illum})\n\n"
            f"💡 *নিচের বাটনগুলো চেপে ২৪ ঘণ্টা, ৭ দিনের পূর্বাভাস বা স্মার্ট পরামর্শ দেখুন।*"
        )
    else:
        return (
            f"🌦️ **Real-Time Weather Overview — {city_name}**\n"
            f"──────────────────────\n\n"
            f"🌡️ **Temperature & Conditions:**\n"
            f"• Current Temp: **{temp_str}** (Feels like: {feels_str})\n"
            f"• Sky Condition: {cond_emoji} {cond_text}\n"
            f"• Today's Range: {min_t_str} to {max_t_str}\n\n"
            f"💧 **Humidity & Wind:**\n"
            f"• Humidity: {humidity}% | Dew Point: {dew_str}\n"
            f"• Wind Speed: {wind_speed:.1f} km/h ({wind_dir})\n"
            f"• Pressure: {pressure:.0f} hPa\n\n"
            f"🌧️ **Rain & Visibility:**\n"
            f"• Rain Probability: {rain_prob}% (Rainfall: {rainfall:.1f} mm)\n"
            f"• Cloud Cover: {clouds}%\n"
            f"• Visibility: {visibility:.1f} km\n\n"
            f"☀️ **Sun, Moon & Air Quality:**\n"
            f"• Air Quality (AQI): {aqi_val} ({aqi_cat} {aqi_emoji})\n"
            f"• UV Index: {uv:.1f} ({uv_cat} {uv_emoji})\n"
            f"• Sunrise: {sunrise} | Sunset: {sunset}\n"
            f"• Moon Phase: {moon_emoji} {moon_name} ({moon_illum})\n\n"
            f"──────────────────────\n"
            f"💡 *Use the buttons below to explore 24h, 7-day forecasts, or smart advice:*"
        )

async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /weather [city] command."""
    user = update.effective_user
    if not is_authorized(user.id):
        await update.message.reply_text(ACCESS_DENIED_MESSAGE_BN, parse_mode="Markdown")
        return

    db_user = await get_or_create_user(user.id, user.username, user.first_name)
    lang = db_user.get("language", "bn")
    unit = db_user.get("temp_unit", "C")

    # City query from command args
    args = context.args
    query = " ".join(args).strip() if args else ""
    
    if not query:
        query = db_user.get("default_city") or "Dhaka"

    # Search city
    cities = await search_city(query)
    if not cities:
        err_msg = f"❌ '{query}' শহরটি খুঁজে পাওয়া যায়নি। অনুগ্রহ করে বানান ঠিক করে পুনরায় লিখুন।" if lang == "bn" else f"❌ City '{query}' not found. Please verify spelling."
        await update.message.reply_text(err_msg)
        return

    city = cities[0]
    await log_search(user.id, city["name"])
    
    data = await get_weather_data(city["lat"], city["lon"], unit)
    if not data:
        await update.message.reply_text("⚠️ আবহাওয়ার ডেটা লোড করতে সমস্যা হচ্ছে। কিছুক্ষণ পর চেষ্টা করুন।" if lang == "bn" else "⚠️ Could not fetch weather. Please try again later.")
        return

    card = format_current_weather_card(data, city["display_name"], lang, unit)
    markup = build_weather_buttons(city["lat"], city["lon"], city["name"], lang)
    await update.message.reply_text(card, parse_mode="Markdown", reply_markup=markup)

async def random_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /random command to fetch weather for a random Bangladesh upazila."""
    user = update.effective_user
    if not is_authorized(user.id):
        await update.message.reply_text(ACCESS_DENIED_MESSAGE_BN, parse_mode="Markdown")
        return

    import random
    from services.bd_geocoder import _BD_LOCATIONS, find_bd_location
    db_user = await get_or_create_user(user.id, user.username, user.first_name)
    lang = db_user.get("language", "bn")
    unit = db_user.get("temp_unit", "C")

    upazilas = [l for l in _BD_LOCATIONS if l.get("type") == "upazila"]
    if upazilas:
        chosen = random.choice(upazilas)
        city = find_bd_location(chosen["name_en"]) or chosen
        await log_search(user.id, city["name"])
        data = await get_weather_data(city["lat"], city["lon"], unit)
        if data:
            card = format_current_weather_card(data, city["display_name"], lang, unit)
            markup = build_weather_buttons(city["lat"], city["lon"], city["name"], lang)
            await update.message.reply_text(card, parse_mode="Markdown", reply_markup=markup)

async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle native GPS location attachment."""
    user = update.effective_user
    if not is_authorized(user.id):
        await update.message.reply_text(ACCESS_DENIED_MESSAGE_BN, parse_mode="Markdown")
        return

    loc = update.message.location
    lat = loc.latitude
    lon = loc.longitude
    db_user = await get_or_create_user(user.id, user.username, user.first_name)
    lang = db_user.get("language", "bn")
    unit = db_user.get("temp_unit", "C")

    data = await get_weather_data(lat, lon, unit)
    if not data:
        await update.message.reply_text("⚠️ আপনার লোকেশনের ডেটা পাওয়া যায়নি।" if lang == "bn" else "⚠️ Could not fetch weather for your location.")
        return

    loc_title = "আপনার বর্তমান অবস্থান (Live Location)" if lang == "bn" else "Your Live Location"
    card = format_current_weather_card(data, loc_title, lang, unit)
    markup = build_weather_buttons(lat, lon, "My Location", lang)
    await update.message.reply_text(card, parse_mode="Markdown", reply_markup=markup)

async def weather_callback_dispatcher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callbacks from weather inline buttons (ref, adv, hr, fc)."""
    query = update.callback_query
    user = update.effective_user
    if not is_authorized(user.id):
        await query.answer("⛔ অ্যাক্সেস সীমাবদ্ধ! আপনি এই বটের অনুমোদিত অ্যাডমিন নন।", show_alert=True)
        return

    await query.answer()

    data_str = query.data
    parts = data_str.split(":")
    if len(parts) < 4:
        return

    action, lat_s, lon_s, city_name = parts[0], parts[1], parts[2], ":".join(parts[3:])
    lat, lon = float(lat_s), float(lon_s)

    db_user = await get_or_create_user(user.id)
    lang = db_user.get("language", "bn")
    unit = db_user.get("temp_unit", "C")

    weather_data = await get_weather_data(lat, lon, unit)
    if not weather_data:
        await query.edit_message_text("⚠️ ডেটা রিলোড করা যায়নি।")
        return

    if action == "ref":
        card = format_current_weather_card(weather_data, city_name, lang, unit)
        markup = build_weather_buttons(lat, lon, city_name, lang)
        try:
            await query.edit_message_text(card, parse_mode="Markdown", reply_markup=markup)
        except Exception:
            pass  # Message is identical

    elif action == "adv":
        rec = generate_recommendations(weather_data, lang)
        msg = format_recommendations_message(rec, city_name, lang)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=msg, parse_mode="Markdown")

    elif action == "hr":
        from handlers.forecast_handler import format_hourly_message
        msg = format_hourly_message(weather_data, city_name, lang, unit)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=msg, parse_mode="Markdown")

    elif action == "fc":
        from handlers.forecast_handler import format_daily_forecast_message
        msg = format_daily_forecast_message(weather_data, city_name, lang, unit)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=msg, parse_mode="Markdown")
