"""
Conversational Weather Assistant Handler:
Processes natural language questions ("আজ কি বৃষ্টি হবে?", "ছাতা লাগবে?"),
menu buttons, route questions, and raw city names.
"""
from telegram import Update
from telegram.ext import ContextTypes
from database.db import get_or_create_user
from services.nlp_parser import classify_intent
from services.weather_api import search_city, get_weather_data, format_temp
from services.recommendations import generate_recommendations, format_recommendations_message
from services.agriculture import get_agriculture_advice
from services.charts import generate_weather_chart
from services.travel import plan_travel
from handlers.weather_handler import format_current_weather_card, build_weather_buttons
from handlers.forecast_handler import format_hourly_message, format_daily_forecast_message, format_air_quality_message
from handlers.user_handlers import settings_command
from utils.i18n import TERMINOLOGY_EXPLANATIONS, get_wmo_description
from services.gemini_service import ask_gemini

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Dispatcher for free-form user messages and keyboard buttons."""
    text = update.message.text.strip()
    user = update.effective_user
    db_user = await get_or_create_user(user.id, user.username, user.first_name)
    
    if db_user.get("is_blocked", 0) == 1:
        return  # Ignore blocked users

    lang = db_user.get("language", "bn")
    unit = db_user.get("temp_unit", "C")
    default_city = db_user.get("default_city") or "Dhaka"

    # 1. Handle Main Keyboard Button Clicks
    if text in ["🌦️ ঢাকা আবহাওয়া", "🌦️ Dhaka Weather"]:
        cities = await search_city("Dhaka")
        if cities:
            c = cities[0]
            w = await get_weather_data(c["lat"], c["lon"], unit)
            if w:
                await update.message.reply_text(
                    format_current_weather_card(w, c["display_name"], lang, unit),
                    parse_mode="Markdown",
                    reply_markup=build_weather_buttons(c["lat"], c["lon"], c["name"], lang)
                )
        return

    if text in ["📊 গ্রাফ চার্ট", "📊 Weather Chart"]:
        cities = await search_city(default_city)
        if cities:
            c = cities[0]
            w = await get_weather_data(c["lat"], c["lon"], unit)
            if w:
                chart = generate_weather_chart(w, c["name"], lang)
                if chart:
                    caption = f"📊 **{c['display_name']}** এর ২৪ ঘণ্টার তাপমাত্রা ও বৃষ্টির চার্ট"
                    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=chart, caption=caption, parse_mode="Markdown")
        return

    if text in ["📆 ২৪ ঘণ্টা পূর্বাভাস", "📆 24h Hourly Forecast"]:
        cities = await search_city(default_city)
        if cities:
            c = cities[0]
            w = await get_weather_data(c["lat"], c["lon"], unit)
            if w:
                await update.message.reply_text(format_hourly_message(w, c["display_name"], lang, unit), parse_mode="Markdown")
        return

    if text in ["📅 ৭ দিনের পূর্বাভাস", "📅 7-Day Forecast"]:
        cities = await search_city(default_city)
        if cities:
            c = cities[0]
            w = await get_weather_data(c["lat"], c["lon"], unit)
            if w:
                await update.message.reply_text(format_daily_forecast_message(w, c["display_name"], lang, unit), parse_mode="Markdown")
        return

    if text in ["🧠 স্মার্ট পরামর্শ", "🧠 Smart Advice"]:
        cities = await search_city(default_city)
        if cities:
            c = cities[0]
            w = await get_weather_data(c["lat"], c["lon"], unit)
            if w:
                rec = generate_recommendations(w, lang)
                await update.message.reply_text(format_recommendations_message(rec, c["display_name"], lang), parse_mode="Markdown")
        return

    if text in ["🌾 কৃষি মোড", "🌾 Agriculture Mode"]:
        cities = await search_city(default_city)
        if cities:
            c = cities[0]
            w = await get_weather_data(c["lat"], c["lon"], unit)
            if w:
                await update.message.reply_text(get_agriculture_advice(w, c["display_name"], lang), parse_mode="Markdown")
        return

    if text in ["🌫️ এয়ার কোয়ালিটি", "🌫️ Air Quality"]:
        cities = await search_city(default_city)
        if cities:
            c = cities[0]
            w = await get_weather_data(c["lat"], c["lon"], unit)
            if w:
                await update.message.reply_text(format_air_quality_message(w, c["display_name"], lang), parse_mode="Markdown")
        return

    if text in ["⚙️ সেটিংস ও অ্যালার্ট", "⚙️ Settings & Alerts"]:
        await settings_command(update, context)
        return

    # 2. Run NLP Intent Classification
    intent_data = classify_intent(text)
    intent = intent_data["intent"]
    target_city = intent_data.get("city") or default_city

    # Terminology Explanation intent
    if intent == "explain":
        term = intent_data.get("term", "humidity")
        explanation = TERMINOLOGY_EXPLANATIONS.get(term, {}).get(lang, "ব্যাখ্যা পাওয়া যায়নি।")
        await update.message.reply_text(explanation, parse_mode="Markdown")
        return

    # Travel Intent
    if intent == "travel":
        orig = intent_data.get("origin")
        dest = intent_data.get("destination")
        travel_res = await plan_travel(orig, dest, lang)
        if travel_res:
            await update.message.reply_text(travel_res, parse_mode="Markdown")
        else:
            await update.message.reply_text(f"❌ '{orig}' থেকে '{dest}' এর ভ্রমণ আবহাওয়া পাওয়া যায়নি।")
        return

    # Weather-specific intents: rain, umbrella, temp, outdoor, wind, aqi
    if intent in ["rain", "umbrella", "temp", "outdoor", "wind", "aqi"]:
        eff_city = target_city or default_city
        cities = await search_city(eff_city)
        if not cities:
            await update.message.reply_text(f"❌ '{eff_city}' শহর খুঁজে পাওয়া যায়নি।")
            return

        city = cities[0]
        w_data = await get_weather_data(city["lat"], city["lon"], unit)
        if not w_data:
            await update.message.reply_text("⚠️ আবহাওয়ার তথ্য আনা সম্ভব হয়নি।")
            return

        cur = w_data["current"]
        rain_prob = cur.get("today_rain_chance_max", 0)
        rainfall = cur.get("rainfall_amount", 0.0)
        temp = cur.get("temp", 25.0)
        feels = cur.get("feels_like", temp)
        cond_text, emoji = get_wmo_description(cur.get("wmo_code", 0), lang)

        if intent == "rain":
            if rain_prob > 40 or rainfall > 0.2:
                reply = (
                    f"🌧️ হ্যাঁ, **{city['name']}**-এ আজ বৃষ্টির সম্ভাবনা অনেক বেশি ({rain_prob}%)!\n"
                    f"বর্তমান আবহাওয়া: {emoji} {cond_text}। বাইরে গেলে সাথে ছাতা রাখা জরুরি।"
                    if lang == "bn" else
                    f"🌧️ Yes, high chance of rain today in **{city['name']}** ({rain_prob}%)!\n"
                    f"Current condition: {emoji} {cond_text}. Keep an umbrella handy."
                )
            else:
                reply = (
                    f"☀️ না, **{city['name']}**-এ আজ বৃষ্টির সম্ভাবনা বেশ কম ({rain_prob}%)।\n"
                    f"বর্তমান আবহাওয়া: {emoji} {cond_text}, তাপমাত্রা: {temp:.1f}°C।"
                    if lang == "bn" else
                    f"☀️ No, low chance of rain in **{city['name']}** today ({rain_prob}%).\n"
                    f"Current weather: {emoji} {cond_text}, Temperature: {temp:.1f}°C."
                )
            await update.message.reply_text(reply, parse_mode="Markdown")
            return

        if intent == "umbrella":
            rec = generate_recommendations(w_data, lang)
            reply = (
                f"☂️ **{city['name']} ছাতা আপডেট:**\n{rec['umbrella']}"
                if lang == "bn" else
                f"☂️ **{city['name']} Umbrella Update:**\n{rec['umbrella']}"
            )
            await update.message.reply_text(reply, parse_mode="Markdown")
            return

        if intent == "temp":
            reply = (
                f"🌡️ **{city['name']}**-এ বর্তমান তাপমাত্রা {temp:.1f}°C (যা অনুভূত হচ্ছে {feels:.1f}°C)।\n"
                f"আজকের সর্বোচ্চ তাপমাত্রা {cur.get('today_max_temp'):.1f}°C এবং সর্বনিম্ন {cur.get('today_min_temp'):.1f}°C।"
                if lang == "bn" else
                f"🌡️ In **{city['name']}**, temperature is {temp:.1f}°C (feels like {feels:.1f}°C).\n"
                f"Today's high is {cur.get('today_max_temp'):.1f}°C and low is {cur.get('today_min_temp'):.1f}°C."
            )
            await update.message.reply_text(reply, parse_mode="Markdown")
            return

        if intent == "outdoor":
            rec = generate_recommendations(w_data, lang)
            reply = (
                f"🏃 **{city['name']} আউটডোর আপডেট:**\n{rec['outdoor']}\n\n"
                f"আকাশ: {emoji} {cond_text} | তাপমাত্রা: {temp:.1f}°C"
                if lang == "bn" else
                f"🏃 **{city['name']} Outdoor Advice:**\n{rec['outdoor']}\n\n"
                f"Sky: {emoji} {cond_text} | Temp: {temp:.1f}°C"
            )
            await update.message.reply_text(reply, parse_mode="Markdown")
            return

        if intent == "wind":
            wind_spd = cur.get("wind_speed", 0.0)
            reply = (
                f"💨 **{city['name']}**-এ বাতাসের গতিবেগ {wind_spd:.1f} কিমি/ঘণ্টা।\n"
                f"{'⚠️ বাতাস বেশ তীব্র, সাবধানে থাকুন।' if wind_spd > 30 else 'বাতাস স্বাভাবিক ও শান্ত রয়েছে।'}"
                if lang == "bn" else
                f"💨 Wind speed in **{city['name']}** is {wind_spd:.1f} km/h.\n"
                f"{'⚠️ Strong winds detected, take caution.' if wind_spd > 30 else 'Wind is calm and pleasant.'}"
            )
            await update.message.reply_text(reply, parse_mode="Markdown")
            return

        if intent == "aqi":
            reply = format_air_quality_message(w_data, city["display_name"], lang)
            await update.message.reply_text(reply, parse_mode="Markdown")
            return

    # Explicit general weather intent (e.g. "আজকে আবহাওয়া কেমন", "Dhaka weather")
    if intent == "general_weather":
        eff_city = target_city or default_city
        cities = await search_city(eff_city)
        if cities:
            city = cities[0]
            w_data = await get_weather_data(city["lat"], city["lon"], unit)
            if w_data:
                card = format_current_weather_card(w_data, city["display_name"], lang, unit)
                markup = build_weather_buttons(city["lat"], city["lon"], city["name"], lang)
                await update.message.reply_text(card, parse_mode="Markdown", reply_markup=markup)
                return

    # Check if the user solely typed a standalone city name (e.g. "Paris", "Tokyo", "বরিশাল")
    words = text.split()
    question_triggers = [
        '?', 'কী', 'কি', 'কেন', 'কে', 'কোন', 'কোথায়', 'কিভাবে', 'কার', 'বল', 'বলো', 'লিখ', 'লেখ',
        'how', 'why', 'what', 'who', 'where', 'when', 'tell', 'write', 'explain', 'suggest',
        'কৌতুক', 'কবিতা', 'গল্প', 'নাম', 'খাবার', 'কোড', 'code', 'python', 'help', 'hi', 'hello', 'hey'
    ]
    is_conversational = any(q in text.lower() for q in question_triggers) or len(words) > 3

    if not is_conversational and len(text) < 30:
        found_cities = await search_city(text.strip())
        if found_cities:
            c0 = found_cities[0]
            clean_input = text.strip().lower()
            if clean_input in c0["name"].lower() or clean_input in c0.get("display_name", "").lower():
                w_data = await get_weather_data(c0["lat"], c0["lon"], unit)
                if w_data:
                    card = format_current_weather_card(w_data, c0["display_name"], lang, unit)
                    markup = build_weather_buttons(c0["lat"], c0["lon"], c0["name"], lang)
                    await update.message.reply_text(card, parse_mode="Markdown", reply_markup=markup)
                    return

    # 3. Everything else: General Knowledge, Q&A, Chit-chat -> Google Gemini AI!
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    except Exception:
        pass

    ai_response = await ask_gemini(user.id, text, lang)
    try:
        await update.message.reply_text(ai_response, parse_mode="Markdown")
    except Exception:
        await update.message.reply_text(ai_response)
