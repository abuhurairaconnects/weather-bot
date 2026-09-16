"""
Weather Handler: /weather, Location sharing, and Interactive Inline Button dispatcher.
Displays all 16+ basic weather metrics and links to smart sub-views.
"""
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database.db import get_or_create_user, log_search, add_favorite
from services.weather_api import search_city, get_weather_data, format_temp
from utils.i18n import get_wmo_description, get_wind_direction, get_aqi_category, get_uv_category
from services.recommendations import generate_recommendations, format_recommendations_message
from services.agriculture import get_agriculture_advice
from services.charts import generate_weather_chart

def build_weather_buttons(lat: float, lon: float, city_name: str, lang: str = "bn") -> InlineKeyboardMarkup:
    """Build inline keyboard for a specific location."""
    c_short = city_name.split(",")[0].strip()[:15]
    if lang == "bn":
        keyboard = [
            [
                InlineKeyboardButton("🔄 রিফ্রেশ", callback_data=f"ref:{lat:.4f}:{lon:.4f}:{c_short}"),
                InlineKeyboardButton("📊 গ্রাফ চার্ট", callback_data=f"crt:{lat:.4f}:{lon:.4f}:{c_short}")
            ],
            [
                InlineKeyboardButton("📆 ২৪ ঘণ্টা", callback_data=f"hr:{lat:.4f}:{lon:.4f}:{c_short}"),
                InlineKeyboardButton("📅 ৭ দিন", callback_data=f"fc:{lat:.4f}:{lon:.4f}:{c_short}")
            ],
            [
                InlineKeyboardButton("🌫️ এয়ার কোয়ালিটি", callback_data=f"aqi:{lat:.4f}:{lon:.4f}:{c_short}"),
                InlineKeyboardButton("🧠 স্মার্ট পরামর্শ", callback_data=f"adv:{lat:.4f}:{lon:.4f}:{c_short}")
            ],
            [
                InlineKeyboardButton("🌾 কৃষি মোড", callback_data=f"agr:{lat:.4f}:{lon:.4f}:{c_short}"),
                InlineKeyboardButton("⭐ ফেভারিট সেভ", callback_data=f"fav:{lat:.4f}:{lon:.4f}:{c_short}")
            ]
        ]
    else:
        keyboard = [
            [
                InlineKeyboardButton("🔄 Refresh", callback_data=f"ref:{lat:.4f}:{lon:.4f}:{c_short}"),
                InlineKeyboardButton("📊 Chart", callback_data=f"crt:{lat:.4f}:{lon:.4f}:{c_short}")
            ],
            [
                InlineKeyboardButton("📆 24h Hourly", callback_data=f"hr:{lat:.4f}:{lon:.4f}:{c_short}"),
                InlineKeyboardButton("📅 7-Day", callback_data=f"fc:{lat:.4f}:{lon:.4f}:{c_short}")
            ],
            [
                InlineKeyboardButton("🌫️ Air Quality", callback_data=f"aqi:{lat:.4f}:{lon:.4f}:{c_short}"),
                InlineKeyboardButton("🧠 Smart Advice", callback_data=f"adv:{lat:.4f}:{lon:.4f}:{c_short}")
            ],
            [
                InlineKeyboardButton("🌾 Agriculture", callback_data=f"agr:{lat:.4f}:{lon:.4f}:{c_short}"),
                InlineKeyboardButton("⭐ Save Favorite", callback_data=f"fav:{lat:.4f}:{lon:.4f}:{c_short}")
            ]
        ]
    return InlineKeyboardMarkup(keyboard)

def format_current_weather_card(data: dict, city_name: str, lang: str = "bn", unit: str = "C") -> str:
    """Format full 16-parameter weather status card."""
    cur = data["current"]
    wmo_code = cur.get("wmo_code", 0)
    cond_text, cond_emoji = get_wmo_description(wmo_code, lang)
    
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
            f"🌦️ **আবহাওয়া পরিস্থিতি — {city_name}**\n"
            f"──────────────────────\n\n"
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
            f"──────────────────────\n"
            f"💡 *নিচের বাটন চেপে চার্ট, পূর্বাভাস ও পরামর্শ দেখুন:*"
        )
    else:
        return (
            f"🌦️ **Weather Overview — {city_name}**\n"
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
            f"💡 *Use the buttons below to explore charts and advice:*"
        )

async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /weather [city] command."""
    user = update.effective_user
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

async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle native GPS location attachment."""
    loc = update.message.location
    lat = loc.latitude
    lon = loc.longitude
    user = update.effective_user
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
    """Handle callbacks from weather inline buttons."""
    query = update.callback_query
    await query.answer()

    data_str = query.data
    parts = data_str.split(":")
    if len(parts) < 4:
        return

    action, lat_s, lon_s, city_name = parts[0], parts[1], parts[2], ":".join(parts[3:])
    lat, lon = float(lat_s), float(lon_s)

    user = update.effective_user
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

    elif action == "crt":
        chart_buf = generate_weather_chart(weather_data, city_name, lang)
        if chart_buf:
            caption = f"📊 **{city_name}** এর পরবর্তী ২৪ ঘণ্টার আবহাওয়া চিত্র" if lang == "bn" else f"📊 24-hour weather visual analytics for **{city_name}**"
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=chart_buf, caption=caption, parse_mode="Markdown")

    elif action == "adv":
        rec = generate_recommendations(weather_data, lang)
        msg = format_recommendations_message(rec, city_name, lang)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=msg, parse_mode="Markdown")

    elif action == "agr":
        agri_msg = get_agriculture_advice(weather_data, city_name, lang)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=agri_msg, parse_mode="Markdown")

    elif action == "hr":
        from handlers.forecast_handler import format_hourly_message
        msg = format_hourly_message(weather_data, city_name, lang, unit)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=msg, parse_mode="Markdown")

    elif action == "fc":
        from handlers.forecast_handler import format_daily_forecast_message
        msg = format_daily_forecast_message(weather_data, city_name, lang, unit)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=msg, parse_mode="Markdown")

    elif action == "aqi":
        from handlers.forecast_handler import format_air_quality_message
        msg = format_air_quality_message(weather_data, city_name, lang)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=msg, parse_mode="Markdown")

    elif action == "fav":
        await add_favorite(user.id, "custom", city_name, lat, lon)
        fav_confirm = f"⭐ **{city_name}** সফলভাবে আপনার ফেভারিট তালিকায় যুক্ত হয়েছে!" if lang == "bn" else f"⭐ **{city_name}** added to your favorites!"
        await query.answer(fav_confirm, show_alert=True)
