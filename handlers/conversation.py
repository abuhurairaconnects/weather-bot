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
from handlers.weather_handler import format_current_weather_card, build_weather_buttons
from handlers.forecast_handler import format_hourly_message, format_daily_forecast_message, format_air_quality_message
from handlers.common import get_main_keyboard
from handlers.division_handler import show_divisions_menu, show_lightning_divisions_menu
from utils.i18n import TERMINOLOGY_EXPLANATIONS, get_wmo_description
from services.gemini_service import ask_gemini
from config import is_authorized, ACCESS_DENIED_MESSAGE_BN

import time
from typing import Dict

# Smart Session Greeting: track last active timestamp per user_id
_USER_LAST_ACTIVE: Dict[int, float] = {}
GREETING_COOLDOWN_SECONDS = 1200  # 20 minutes cooldown before showing intro again

def get_smart_signature_greeting(user_id: int, lang: str = "bn") -> str:
    """Returns the Abu Huraira AI greeting ONLY on first interaction or after 20+ mins of inactivity."""
    now = time.time()
    last_time = _USER_LAST_ACTIVE.get(user_id, 0.0)
    _USER_LAST_ACTIVE[user_id] = now

    if now - last_time > GREETING_COOLDOWN_SECONDS:
        return (
            "👋 **আসসালামু আলাইকুম, আমি আবু হুরাইরার AI অ্যাসিস্ট্যান্ট, আপনাকে কীভাবে সাহায্য করি?**\n\n"
            if lang == "bn" else
            "👋 **Assalamu Alaikum, I am Abu Huraira's AI Assistant, how can I help you?**\n\n"
        )
    return ""

async def safe_reply(update: Update, text: str, reply_markup=None):
    """Safely reply with Markdown, falling back to plain text if entity parsing fails."""
    try:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    except Exception:
        clean = text.replace("*", "").replace("`", "").replace("_", "")
        await update.message.reply_text(clean, reply_markup=reply_markup)

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Dispatcher for free-form user messages and keyboard buttons."""
    user = update.effective_user
    if not is_authorized(user.id):
        await update.message.reply_text(ACCESS_DENIED_MESSAGE_BN, parse_mode="Markdown")
        return

    text = update.message.text.strip()
    db_user = await get_or_create_user(user.id, user.username, user.first_name)
    
    if db_user.get("is_blocked", 0) == 1:
        return  # Ignore blocked users

    lang = db_user.get("language", "bn")
    unit = db_user.get("temp_unit", "C")
    default_city = db_user.get("default_city") or "Dhaka"

    # Smart signature greeting: only non-empty on first message or after 20+ minutes of idle time
    signature_greeting = get_smart_signature_greeting(user.id, lang)

    # 1. Handle Main Streamlined Keyboard Button Clicks
    # A. Division button (বিভাগ নির্বাচন)
    if text in ["🏢 বিভাগ", "বিভাগ", "🏢 Divisions", "Divisions"]:
        await show_divisions_menu(update, context)
        return

    # B. 24-Hour Forecast (২৪ ঘণ্টার পূর্বাভাস)
    if text in ["📆 ২৪ ঘণ্টার পূর্বাভাস", "📆 ২৪ ঘণ্টা পূর্বাভাস", "২৪ ঘণ্টার পূর্বাভাস", "২৪ ঘণ্টা পূর্বাভাস", "📆 24-Hour Forecast", "24-Hour Forecast", "24h"]:
        cities = await search_city(default_city)
        if cities:
            c = cities[0]
            w = await get_weather_data(c["lat"], c["lon"], unit)
            if w:
                await safe_reply(update, format_hourly_message(w, c["display_name"], lang, unit), reply_markup=get_main_keyboard(lang))
        return

    # C. 7-Day Forecast (৭ দিনের পূর্বাভাস)
    if text in ["📅 ৭ দিনের পূর্বাভাস", "৭ দিনের পূর্বাভাস", "📅 7-Day Forecast", "7-Day Forecast", "7d"]:
        cities = await search_city(default_city)
        if cities:
            c = cities[0]
            w = await get_weather_data(c["lat"], c["lon"], unit)
            if w:
                await safe_reply(update, format_daily_forecast_message(w, c["display_name"], lang, unit), reply_markup=get_main_keyboard(lang))
        return

    # D. Lightning & Severe Storm Alert (বজ্রপাত সতর্কতা)
    if text in [
        "⚡ বজ্রপাত সতর্কতা", "⚡ বজ্রপাত ও ঝড় সতর্কতা", "⚡ বজ্রপাত আপডেট",
        "বজ্রপাত সতর্কতা", "বজ্রপাত ও ঝড় সতর্কতা", "বজ্রপাত আপডেট", "বজ্রপাত",
        "⚡ Lightning Alert", "Lightning Alert", "⚡ Severe Weather Alert", "lightning", "thunder"
    ]:
        await show_lightning_divisions_menu(update, context)
        return

    # E. Subscription / Unsubscription NLP shortcuts
    lower_text = text.lower()
    if any(k in lower_text for k in ["আনসাবস্ক্রাইব", "unsubscribe", "অ্যালার্ট বন্ধ", "নোটিফিকেশন বন্ধ", "বুলেটিন বন্ধ"]):
        from handlers.user_handlers import unsubscribe_command
        await unsubscribe_command(update, context)
        return

    if any(k in lower_text for k in ["সাবস্ক্রাইব", "subscribe", "সকাল সাতটা", "সন্ধ্যা সাতটা", "অটোমেটিক আপডেট", "দৈনিক বুলেটিন", "অ্যালার্ট চালু"]):
        from handlers.user_handlers import subscribe_command
        await subscribe_command(update, context)
        return

    # Direct Bangladesh Location Check (instant 0ms response for any of 64 districts & 495+ upazilas)
    from services.bd_geocoder import find_bd_location
    bd_loc = find_bd_location(text)
    if bd_loc:
        w_data = await get_weather_data(bd_loc["lat"], bd_loc["lon"], unit)
        if w_data:
            card = format_current_weather_card(w_data, bd_loc["display_name"], lang, unit)
            markup = build_weather_buttons(bd_loc["lat"], bd_loc["lon"], bd_loc["name"], lang)
            msg = signature_greeting + card if signature_greeting else card
            await safe_reply(update, msg, reply_markup=markup)
            return

    # 2. Run NLP Intent Classification
    intent_data = classify_intent(text)
    intent = intent_data["intent"]
    target_city = intent_data.get("city") or default_city

    # Terminology Explanation intent
    if intent == "explain":
        term = intent_data.get("term", "humidity")
        explanation = TERMINOLOGY_EXPLANATIONS.get(term, {}).get(lang, "ব্যাখ্যা পাওয়া যায়নি।")
        msg = signature_greeting + explanation if signature_greeting else explanation
        await safe_reply(update, msg)
        return

    # Weather-specific intents: rain, umbrella, temp, outdoor, wind, aqi
    if intent in ["rain", "umbrella", "temp", "outdoor", "wind", "aqi"]:
        eff_city = target_city or default_city
        cities = await search_city(eff_city)
        if not cities:
            await safe_reply(
                update,
                f"⚠️ দুঃখিত, '{eff_city}' খুঁজে পাওয়া যায়নি।\n"
                "এই বটটি শুধুমাত্র বাংলাদেশের সকল জেলা ও উপজেলার আবহাওয়া তথ্যের জন্য নিবেদিত। "
                "বাংলাদেশের বাইরের কোনো স্থান এখানে প্রদান করা হয় না। অনুগ্রহ করে বাংলাদেশের কোনো জেলা বা উপজেলার নাম লিখুন।"
                if lang == "bn" else
                f"⚠️ Sorry, '{eff_city}' was not found.\n"
                "This bot is dedicated strictly to all districts and upazilas in Bangladesh. "
                "Foreign locations are not supported. Please enter a location within Bangladesh."
            )
            return

        city = cities[0]
        w_data = await get_weather_data(city["lat"], city["lon"], unit)
        if not w_data:
            await safe_reply(update, "⚠️ আবহাওয়ার তথ্য আনা সম্ভব হয়নি।")
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
            await safe_reply(update, signature_greeting + reply if signature_greeting else reply)
            return

        if intent == "umbrella":
            rec = generate_recommendations(w_data, lang)
            reply = (
                f"☂️ **{city['name']} ছাতা আপডেট:**\n{rec['umbrella']}"
                if lang == "bn" else
                f"☂️ **{city['name']} Umbrella Update:**\n{rec['umbrella']}"
            )
            await safe_reply(update, signature_greeting + reply if signature_greeting else reply)
            return

        if intent == "temp":
            reply = (
                f"🌡️ **{city['name']}**-এ বর্তমান তাপমাত্রা {temp:.1f}°C (যা অনুভূত হচ্ছে {feels:.1f}°C)।\n"
                f"আজকের সর্বোচ্চ তাপমাত্রা {cur.get('today_max_temp'):.1f}°C এবং সর্বনিম্ন {cur.get('today_min_temp'):.1f}°C।"
                if lang == "bn" else
                f"🌡️ In **{city['name']}**, temperature is {temp:.1f}°C (feels like {feels:.1f}°C).\n"
                f"Today's high is {cur.get('today_max_temp'):.1f}°C and low is {cur.get('today_min_temp'):.1f}°C."
            )
            await safe_reply(update, signature_greeting + reply if signature_greeting else reply)
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
            await safe_reply(update, signature_greeting + reply if signature_greeting else reply)
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
            await safe_reply(update, signature_greeting + reply if signature_greeting else reply)
            return

        if intent == "aqi":
            reply = format_air_quality_message(w_data, city["display_name"], lang)
            await safe_reply(update, signature_greeting + reply if signature_greeting else reply)
            return

    # Explicit general weather intent (e.g. "আজকে আবহাওয়া কেমন", "Dhaka weather", "তাড়াশ")
    if intent == "general_weather":
        eff_city = target_city or default_city
        cities = await search_city(eff_city)
        if cities:
            city = cities[0]
            w_data = await get_weather_data(city["lat"], city["lon"], unit)
            if w_data:
                card = format_current_weather_card(w_data, city["display_name"], lang, unit)
                markup = build_weather_buttons(city["lat"], city["lon"], city["name"], lang)
                msg = signature_greeting + card if signature_greeting else card
                await safe_reply(update, msg, reply_markup=markup)
                return
        else:
            await safe_reply(
                update,
                f"⚠️ দুঃখিত, '{eff_city}' খুঁজে পাওয়া যায়নি।\n"
                "এই বটটি শুধুমাত্র বাংলাদেশের সকল জেলা ও উপজেলার আবহাওয়া সেবার জন্য প্রস্তুত। "
                "বাংলাদেশের বাইরের কোনো স্থান এখানে অন্তর্ভুক্ত নয়। অনুগ্রহ করে বাংলাদেশের কোনো জেলা বা উপজেলার নাম লিখুন।"
                if lang == "bn" else
                f"⚠️ Sorry, '{eff_city}' was not found.\n"
                "This bot is exclusively dedicated to districts and upazilas in Bangladesh. "
                "Foreign locations are not supported. Please enter a location within Bangladesh."
            )
            return

    # Check if the user solely typed a standalone city/upazila name (e.g. "Paris", "Tokyo", "বরিশাল", "তাড়াশ")
    words = text.split()
    question_triggers = [
        '?', 'কী', 'কি', 'কেন', 'কে', 'কোন', 'কোথায়', 'কিভাবে', 'কার', 'বল', 'বলো', 'লিখ', 'লেখ',
        'how', 'why', 'what', 'who', 'where', 'when', 'tell', 'write', 'explain', 'suggest',
        'কৌতুক', 'কবিতা', 'গল্প', 'নাম', 'খাবার', 'কোড', 'code', 'python', 'help', 'hi', 'hello', 'hey'
    ]
    is_conversational = any(q in text.lower() for q in question_triggers) or len(words) > 5

    if not is_conversational and len(text) < 70:
        found_cities = await search_city(text.strip())
        if found_cities:
            c0 = found_cities[0]
            w_data = await get_weather_data(c0["lat"], c0["lon"], unit)
            if w_data:
                card = format_current_weather_card(w_data, c0["display_name"], lang, unit)
                markup = build_weather_buttons(c0["lat"], c0["lon"], c0["name"], lang)
                msg = signature_greeting + card if signature_greeting else card
                await safe_reply(update, msg, reply_markup=markup)
                return

    # 3. Everything else: General Knowledge, Q&A, Chit-chat -> Google Gemini AI!
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    except Exception:
        pass

    ai_response = await ask_gemini(user.id, text, lang)
    
    # Smart greeting handling for AI response:
    greeting_bn = "আসসালামু আলাইকুম, আমি আবু হুরাইরার AI অ্যাসিস্ট্যান্ট, আপনাকে কীভাবে সাহায্য করি?"
    greeting_en = "Assalamu Alaikum, I am Abu Huraira's AI Assistant, how can I help you?"
    if signature_greeting:
        greeting_marker = "আবু হুরাইরার" if lang == "bn" else "Abu Huraira"
        if greeting_marker not in ai_response:
            ai_response = signature_greeting + ai_response
    else:
        # User is in active conversation, strip greeting if Gemini generated it
        ai_response = ai_response.replace(greeting_bn, "").replace(greeting_en, "").strip()

    # Telegram message limit is 4096 characters; chunk cleanly if needed
    if len(ai_response) > 4000:
        for i in range(0, len(ai_response), 4000):
            chunk = ai_response[i:i+4000]
            await safe_reply(update, chunk)
    else:
        await safe_reply(update, ai_response)
