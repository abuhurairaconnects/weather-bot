"""
Background Alert & Daily Report Scheduler.
Monitors rain, severe weather conditions, and triggers daily morning/evening briefs.
"""
from datetime import datetime, timezone, timedelta
from typing import Dict
from telegram.ext import ContextTypes
from database.db import get_all_subscribers_for_alerts, update_user_setting, update_alert_settings, get_alert_settings
from services.weather_api import get_weather_data, format_temp
from utils.i18n import get_wmo_description, get_aqi_category

# Cache to prevent duplicate alert spamming within a cooldown window (4 hours)
_last_rain_alert: Dict[int, datetime] = {}
_last_severe_alert: Dict[int, datetime] = {}
_last_report_date: Dict[str, str] = {}  # key: f"{user_id}:m" or f"{user_id}:e", val: "YYYY-MM-DD"

async def check_rain_and_severe_alerts(context: ContextTypes.DEFAULT_TYPE):
    """
    Periodic job (runs every 30 minutes).
    Checks upcoming precipitation and severe weather for subscribed users.
    """
    subscribers = await get_all_subscribers_for_alerts()
    now = datetime.now(timezone.utc)

    for sub in subscribers:
        user_id = sub["user_id"]
        lat = sub.get("lat")
        lon = sub.get("lon")
        city = sub.get("city_name") or "Your Location"
        lang = sub.get("language", "bn")
        unit = sub.get("temp_unit", "C")
        rain_sub = sub.get("rain_alert", 0) == 1
        severe_sub = sub.get("severe_alert", 1) == 1

        if not lat or not lon:
            continue

        weather_data = await get_weather_data(lat, lon, unit)
        if not weather_data:
            continue

        cur = weather_data.get("current", {})
        hourly = weather_data.get("hourly", {})
        rain_probs = hourly.get("precipitation_probability", [])
        precips = hourly.get("precipitation", [])

        # 1. Rain Alert in Next 1 Hour
        if rain_sub:
            # Check next 1-2 hours
            next_hour_prob = rain_probs[0] if rain_probs else 0
            next_hour_amt = precips[0] if precips else 0.0

            should_alert_rain = (next_hour_prob >= 55) or (next_hour_amt >= 0.8)
            last_alert = _last_rain_alert.get(user_id)
            cooldown_expired = (last_alert is None) or ((now - last_alert) > timedelta(hours=3))

            if should_alert_rain and cooldown_expired:
                _last_rain_alert[user_id] = now
                if lang == "bn":
                    alert_msg = (
                        f"🌧️ **বৃষ্টির তাৎক্ষণিক সতর্কতা! (Rain Alert)**\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"📍 **স্থান:** {city}\n"
                        f"আগামী ১ ঘণ্টার মধ্যে আপনার এলাকায় বৃষ্টি শুরু হওয়ার প্রবল সম্ভাবনা রয়েছে ({next_hour_prob}% সম্ভাবনা)!\n\n"
                        f"☂️ বাইরে থাকলে দ্রুত নিরাপদ আশ্রয়ে যান অথবা সাথে ছাতা রাখুন।"
                    )
                else:
                    alert_msg = (
                        f"🌧️ **Immediate Rain Alert!**\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"📍 **Location:** {city}\n"
                        f"High probability of rain within the next 1 hour ({next_hour_prob}% chance)!\n\n"
                        f"☂️ Please carry an umbrella or seek shelter."
                    )
                try:
                    await context.bot.send_message(chat_id=user_id, text=alert_msg, parse_mode="Markdown")
                except Exception as e:
                    if "blocked" in str(e).lower() or "forbidden" in str(e).lower():
                        await update_user_setting(user_id, "is_blocked", 1)
                    print(f"Failed to send rain alert to {user_id}: {e}")

        # 2. Severe Weather Alert (Thunderstorm, Heavy Storm, Extreme Heat, Extreme AQI)
        if severe_sub:
            wmo_code = cur.get("wmo_code", 0)
            wind_speed = cur.get("wind_speed", 0.0)
            temp = cur.get("temp", 25.0)
            aqi_val = cur.get("aqi", {}).get("us_aqi", 0)

            severe_reasons_bn = []
            severe_reasons_en = []

            if wmo_code in [95, 96, 99]:
                severe_reasons_bn.append("বজ্রপাত ও শিলাবৃষ্টিসহ তীব্র ঝড় (Thunderstorm)")
                severe_reasons_en.append("Thunderstorm with lightning and hail")
            if wind_speed > 45.0:
                severe_reasons_bn.append(f"ঝড়ো হাওয়া (গতিবেগ: {wind_speed:.1f} কিমি/ঘণ্টা)")
                severe_reasons_en.append(f"Gale-force winds ({wind_speed:.1f} km/h)")
            if temp > 39.0:
                severe_reasons_bn.append(f"চরম তীব্র তাপপ্রবাহ (তাপমাত্রা: {temp:.1f}°C)")
                severe_reasons_en.append(f"Extreme Heatwave ({temp:.1f}°C)")
            if aqi_val >= 250:
                severe_reasons_bn.append(f"চরম ঝুঁকিপূর্ণ বায়ু দূষণ (AQI: {aqi_val})")
                severe_reasons_en.append(f"Severe Hazardous Air Quality (AQI: {aqi_val})")

            last_sev = _last_severe_alert.get(user_id)
            sev_cooldown_expired = (last_sev is None) or ((now - last_sev) > timedelta(hours=4))

            if severe_reasons_bn and sev_cooldown_expired:
                _last_severe_alert[user_id] = now
                if lang == "bn":
                    sev_msg = (
                        f"⚠️ **জরুরি আবহাওয়া সতর্কবার্তা (Severe Alert)!**\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"📍 **স্থান:** {city}\n\n"
                        f"সতর্কতার কারণ:\n• " + "\n• ".join(severe_reasons_bn) + "\n\n"
                        f"🛡️ অনুগ্রহ করে সতর্ক থাকুন এবং প্রয়োজনীয় নিরাপত্তা ব্যবস্থা গ্রহণ করুন।"
                    )
                else:
                    sev_msg = (
                        f"⚠️ **Severe Weather Alert!**\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"📍 **Location:** {city}\n\n"
                        f"Hazard Details:\n• " + "\n• ".join(severe_reasons_en) + "\n\n"
                        f"🛡️ Please take necessary safety precautions."
                    )
                try:
                    await context.bot.send_message(chat_id=user_id, text=sev_msg, parse_mode="Markdown")
                except Exception as e:
                    if "blocked" in str(e).lower() or "forbidden" in str(e).lower():
                        await update_user_setting(user_id, "is_blocked", 1)
                    print(f"Failed to send severe alert to {user_id}: {e}")

def build_morning_report_message(w_data: dict, city: str, lang: str = "bn", unit: str = "C") -> str:
    """Format rich 07:00 AM morning bulletin."""
    cur = w_data.get("current", {})
    max_t = format_temp(cur.get("today_max_temp"), unit)
    min_t = format_temp(cur.get("today_min_temp"), unit)
    rain_p = cur.get("today_rain_chance_max", 0)
    wind_s = cur.get("wind_speed", 0.0)
    uv = cur.get("today_max_uv", 0.0)
    aqi_v = cur.get("aqi", {}).get("us_aqi", 0)
    aqi_cat, aqi_emo, _ = get_aqi_category(aqi_v, lang)
    wmo_code = cur.get("wmo_code", 0)
    cond_text, cond_emoji = get_wmo_description(wmo_code, lang)

    # Weather safety recommendation
    advice_bn = ""
    advice_en = ""
    if rain_p >= 50:
        advice_bn = f"\n☂️ **জরুরি সতর্কতা:** আজ বৃষ্টির প্রবল সম্ভাবনা রয়েছে ({rain_p}%), বাইরে বের হলে ছাতা সঙ্গে রাখুন!"
        advice_en = f"\n☂️ **Rain Advisory:** High chance of rain today ({rain_p}%), keep an umbrella handy!"
    elif cur.get("today_max_temp", 25) >= 36:
        advice_bn = "\n☀️ **তাপদাহ সতর্কতা:** আজ তীব্র গরম থাকবে, প্রচুর পানি পান করুন ও সরাসরি রোদ এড়িয়ে চলুন।"
        advice_en = "\n☀️ **Heat Advisory:** Hot day ahead, stay well-hydrated and avoid direct sunlight."
    elif wind_s >= 35:
        advice_bn = f"\n💨 **বাতাস সতর্কতা:** আজ ঝড়ো হাওয়া বইতে পারে (গতিবেগ {wind_s:.1f} কিমি/ঘণ্টা)।"
        advice_en = f"\n💨 **Wind Advisory:** Windy day ahead with gusts up to {wind_s:.1f} km/h."

    if lang == "bn":
        return (
            f"🌅 **সুপ্রভাত! সকালের আবহাওয়া বুলেটিন — {city}**\n"
            f"⏰ *সকাল ০৭:০০ টার নিয়মিত বুলেটিন*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🌤️ **আজকের আকাশ:** {cond_emoji} {cond_text}\n"
            f"🌡️ **তাপমাত্রা পরিসীমা:** {min_t} থেকে {max_t}\n"
            f"🌧️ **বৃষ্টির সম্ভাবনা:** {rain_p}%\n"
            f"💨 **বাতাসের গতিবেগ:** {wind_s:.1f} কিমি/ঘণ্টা\n"
            f"☀️ **ইউভি সূচক (UV):** {uv:.1f}\n"
            f"🌫️ **বায়ুমান (AQI):** {aqi_v} ({aqi_cat} {aqi_emo})"
            f"{advice_bn}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"✨ *আপনার সারাদিনটি শুভ, সুন্দর ও নিরাপদ কাটুক!*"
        )
    else:
        return (
            f"🌅 **Good Morning! Morning Weather Bulletin — {city}**\n"
            f"⏰ *Regular 07:00 AM Bulletin*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🌤️ **Sky Condition:** {cond_emoji} {cond_text}\n"
            f"🌡️ **Today's Range:** {min_t} to {max_t}\n"
            f"🌧️ **Rain Chance:** {rain_p}%\n"
            f"💨 **Wind Speed:** {wind_s:.1f} km/h\n"
            f"☀️ **UV Index:** {uv:.1f}\n"
            f"🌫️ **Air Quality (AQI):** {aqi_v} ({aqi_cat} {aqi_emo})"
            f"{advice_en}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"✨ *Have a safe and productive day!*"
        )

def build_evening_report_message(w_data: dict, city: str, lang: str = "bn", unit: str = "C") -> str:
    """Format rich 07:00 PM evening bulletin with tomorrow's preview."""
    cur = w_data.get("current", {})
    cur_t = format_temp(cur.get("temp"), unit)
    feels_t = format_temp(cur.get("feels_like"), unit)
    cond_t, cond_e = get_wmo_description(cur.get("wmo_code", 0), lang)
    humidity = cur.get("humidity", 0)
    moon = cur.get("moon", {})
    moon_e = moon.get("emoji", "🌕")
    moon_t = moon.get("name_bn" if lang == "bn" else "name_en", "Moon")

    # Tomorrow preview from daily forecast
    daily = w_data.get("daily", {})
    times = daily.get("time", [])
    tomorrow_sec = ""
    if len(times) > 1:
        tom_max = format_temp(daily.get("temperature_2m_max", [0, 0])[1], unit)
        tom_min = format_temp(daily.get("temperature_2m_min", [0, 0])[1], unit)
        tom_rain = daily.get("precipitation_probability_max", [0, 0])[1]
        tom_code = daily.get("weather_code", [0, 0])[1]
        tom_desc, tom_emo = get_wmo_description(tom_code, lang)
        if lang == "bn":
            tomorrow_sec = (
                f"\n📅 **আগামীকালের পূর্বাভাস একনজরে:**\n"
                f"• আকাশ: {tom_emo} {tom_desc}\n"
                f"• তাপমাত্রা: {tom_min} থেকে {tom_max}\n"
                f"• বৃষ্টির সম্ভাবনা: {tom_rain}%\n"
            )
        else:
            tomorrow_sec = (
                f"\n📅 **Tomorrow's Quick Outlook:**\n"
                f"• Sky: {tom_emo} {tom_desc}\n"
                f"• Temperature: {tom_min} to {tom_max}\n"
                f"• Rain Chance: {tom_rain}%\n"
            )

    if lang == "bn":
        return (
            f"🌙 **শুভ সন্ধ্যা! সান্ধ্যকালীন আবহাওয়া আপডেট — {city}**\n"
            f"⏰ *সন্ধ্যা ০৭:০০ টার নিয়মিত বুলেটিন*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🌡️ **বর্তমান রাতের তাপমাত্রা:** {cur_t} (অনুভূত: {feels_t})\n"
            f"{cond_e} **রাতের আবহাওয়া:** {cond_t}\n"
            f"💧 **আর্দ্রতা:** {humidity}%\n"
            f"{moon_e} **চন্দ্রকলা:** {moon_t} ({moon.get('illumination', '')})\n"
            f"━━━━━━━━━━━━━━━━━━━━"
            f"{tomorrow_sec}"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🛌 *একটি আরামদায়ক ও প্রশান্তিময় রাত কামনা করছি।*"
        )
    else:
        return (
            f"🌙 **Good Evening! Night Weather Update — {city}**\n"
            f"⏰ *Regular 07:00 PM Bulletin*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🌡️ **Current Night Temp:** {cur_t} (Feels like: {feels_t})\n"
            f"{cond_e} **Weather Condition:** {cond_t}\n"
            f"💧 **Humidity:** {humidity}%\n"
            f"{moon_e} **Moon Phase:** {moon_t} ({moon.get('illumination', '')})\n"
            f"━━━━━━━━━━━━━━━━━━━━"
            f"{tomorrow_sec}"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🛌 *Wishing you a restful and peaceful night.*"
        )

async def send_single_user_report(bot, user_id: int, report_type: str = "morning") -> bool:
    """Directly send a morning or evening weather report to a user (used by /testdaily or tests)."""
    sub = await get_alert_settings(user_id)
    lat = sub.get("lat") or 23.7115253
    lon = sub.get("lon") or 90.4111451
    city = sub.get("city_name") or "Dhaka"
    lang = "bn"
    unit = "C"

    w_data = await get_weather_data(lat, lon, unit)
    if not w_data:
        return False

    if report_type == "morning":
        msg = build_morning_report_message(w_data, city, lang, unit)
    else:
        msg = build_evening_report_message(w_data, city, lang, unit)

    await bot.send_message(chat_id=user_id, text=msg, parse_mode="Markdown")
    return True

async def check_daily_reports(context: ContextTypes.DEFAULT_TYPE):
    """
    Checks if it's morning (07:00 AM local Bangladesh time) or evening (07:00 PM local Bangladesh time)
    and delivers daily reports to subscribed users.
    Bangladesh Time is UTC+6 (Asia/Dhaka).
    """
    subscribers = await get_all_subscribers_for_alerts()
    now_utc = datetime.now(timezone.utc)
    bd_time = now_utc + timedelta(hours=6)
    today_str = bd_time.strftime("%Y-%m-%d")
    current_hour = bd_time.hour

    for sub in subscribers:
        user_id = sub["user_id"]
        lat = sub.get("lat")
        lon = sub.get("lon")
        city = sub.get("city_name") or "Dhaka"
        lang = sub.get("language", "bn")
        unit = sub.get("temp_unit", "C")
        last_m = sub.get("last_morning_sent")
        last_e = sub.get("last_evening_sent")

        if not lat or not lon:
            continue

        # Morning Report: 07:00 AM Bangladesh Time (hour == 7)
        if sub.get("morning_report", 0) == 1 and current_hour == 7:
            key = f"{user_id}:m"
            if _last_report_date.get(key) != today_str and last_m != today_str:
                _last_report_date[key] = today_str
                await update_alert_settings(user_id, last_morning_sent=today_str)
                w_data = await get_weather_data(lat, lon, unit)
                if w_data:
                    m_msg = build_morning_report_message(w_data, city, lang, unit)
                    try:
                        await context.bot.send_message(chat_id=user_id, text=m_msg, parse_mode="Markdown")
                    except Exception as e:
                        if "blocked" in str(e).lower() or "forbidden" in str(e).lower():
                            await update_user_setting(user_id, "is_blocked", 1)
                        print(f"Failed morning report to {user_id}: {e}")

        # Evening Report: 07:00 PM / 19:00 Bangladesh Time (hour == 19)
        if sub.get("evening_report", 0) == 1 and current_hour == 19:
            key = f"{user_id}:e"
            if _last_report_date.get(key) != today_str and last_e != today_str:
                _last_report_date[key] = today_str
                await update_alert_settings(user_id, last_evening_sent=today_str)
                w_data = await get_weather_data(lat, lon, unit)
                if w_data:
                    e_msg = build_evening_report_message(w_data, city, lang, unit)
                    try:
                        await context.bot.send_message(chat_id=user_id, text=e_msg, parse_mode="Markdown")
                    except Exception as e:
                        if "blocked" in str(e).lower() or "forbidden" in str(e).lower():
                            await update_user_setting(user_id, "is_blocked", 1)
                        print(f"Failed evening report to {user_id}: {e}")

def setup_scheduler(application):
    """Register repeating jobs on the bot's JobQueue."""
    jq = application.job_queue
    if jq:
        # Check alerts every 15 minutes (900 seconds), starting after 45 seconds
        jq.run_repeating(check_rain_and_severe_alerts, interval=900, first=45, name="rain_severe_alerts")
        # Check daily reports every 3 minutes (180 seconds), starting after 60 seconds
        jq.run_repeating(check_daily_reports, interval=180, first=60, name="daily_reports")
        print("✅ Background Weather Alert & Report Schedulers configured (07:00 AM & 07:00 PM BD Time).")
    else:
        print("⚠️ JobQueue not available. Background alerts will not run.")
