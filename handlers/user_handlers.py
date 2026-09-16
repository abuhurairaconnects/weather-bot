"""
User Preferences & Customization Handlers:
/settings, /alerts, /favorites, /location.
Provides interactive inline buttons to change language, units, and notification settings.
"""
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database.db import (
    get_or_create_user, update_user_setting, set_default_location,
    get_favorites, delete_favorite, get_alert_settings, update_alert_settings
)
from services.weather_api import search_city
from handlers.common import get_main_keyboard

def build_settings_keyboard(lang: str, unit: str) -> InlineKeyboardMarkup:
    """Build settings interactive keyboard."""
    lang_label = "বাংলা 🇧🇩 (সক্রিয়)" if lang == "bn" else "Switch to বাংলা 🇧🇩"
    en_label = "English 🇬🇧 (Active)" if lang == "en" else "Switch to English 🇬🇧"
    c_label = "সেলসিয়াস (°C) [Active]" if unit == "C" else "সেলসিয়াস (°C)"
    f_label = "ফারেনহাইট (°F) [Active]" if unit == "F" else "ফারেনহাইট (°F)"

    keyboard = [
        [
            InlineKeyboardButton(lang_label, callback_data="cfg:lang:bn"),
            InlineKeyboardButton(en_label, callback_data="cfg:lang:en")
        ],
        [
            InlineKeyboardButton(c_label, callback_data="cfg:unit:C"),
            InlineKeyboardButton(f_label, callback_data="cfg:unit:F")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def build_alerts_keyboard(alerts: dict, lang: str = "bn") -> InlineKeyboardMarkup:
    """Build alerts toggle keyboard."""
    rain_on = alerts.get("rain_alert", 0) == 1
    severe_on = alerts.get("severe_alert", 1) == 1
    morn_on = alerts.get("morning_report", 0) == 1
    eve_on = alerts.get("evening_report", 0) == 1

    r_btn = f"🌧️ বৃষ্টির অ্যালার্ট: {'চালু ✅' if rain_on else 'বন্ধ ❌'}"
    s_btn = f"⛈️ তীব্র ঝড়/তাপ অ্যালার্ট: {'চালু ✅' if severe_on else 'বন্ধ ❌'}"
    m_btn = f"🌅 সকালের রিপোর্ট (৭টা): {'চালু ✅' if morn_on else 'বন্ধ ❌'}"
    e_btn = f"🌙 সন্ধ্যার রিপোর্ট (৭টা): {'চালু ✅' if eve_on else 'বন্ধ ❌'}"

    keyboard = [
        [InlineKeyboardButton(r_btn, callback_data="alt:rain")],
        [InlineKeyboardButton(s_btn, callback_data="alt:severe")],
        [InlineKeyboardButton(m_btn, callback_data="alt:morning")],
        [InlineKeyboardButton(e_btn, callback_data="alt:evening")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /settings."""
    user = update.effective_user
    db_user = await get_or_create_user(user.id)
    lang = db_user.get("language", "bn")
    unit = db_user.get("temp_unit", "C")
    def_city = db_user.get("default_city") or "Dhaka"

    msg = (
        f"⚙️ **ব্যক্তিগত সেটিংস (Personal Settings)**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 **বর্তমান ভাষা:** {'বাংলা 🇧🇩' if lang == 'bn' else 'English 🇬🇧'}\n"
        f"🌡️ **তাপমাত্রার একক:** {'সেলসিয়াস (°C)' if unit == 'C' else 'ফারেনহাইট (°F)'}\n"
        f"🏠 **ডিফল্ট লোকেশন:** {def_city}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👇 *ভাষা ও একক পরিবর্তন করতে নিচের বাটনে চাপুন:*"
    )
    await update.message.reply_text(
        msg,
        parse_mode="Markdown",
        reply_markup=build_settings_keyboard(lang, unit)
    )

async def alerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /alerts."""
    user = update.effective_user
    db_user = await get_or_create_user(user.id)
    lang = db_user.get("language", "bn")
    alerts = await get_alert_settings(user.id)
    loc_name = alerts.get("city_name") or db_user.get("default_city") or "Dhaka"

    msg = (
        f"🔔 **ওয়েদার অ্যালার্ট ও দৈনিক রিপোর্ট নোটিফিকেশন**\n"
        f"📍 **নির্ধারিত এলাকা:** {loc_name}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"• **বৃষ্টির অ্যালার্ট:** আগামী ১ ঘণ্টার মধ্যে বৃষ্টি শুরু হওয়ার পূর্বাভাস থাকলে জানাবে।\n"
        f"• **তীব্র সতর্কবার্তা:** কালবৈশাখী, বজ্রঝড় বা চরম তাপপ্রবাহের বার্তা।\n"
        f"• **সকালের রিপোর্ট:** প্রতিদিন সকাল ৭:০০ টায় দিনের আবহাওয়ার সারাংশ।\n"
        f"• **সন্ধ্যার রিপোর্ট:** প্রতিদিন সন্ধ্যা ৭:০০ টায় পরবর্তী রাতের আপডেট।\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👇 *চালু বা বন্ধ করতে নিচের বাটনগুলোতে ট্যাপ করুন:*"
    )
    await update.message.reply_text(
        msg,
        parse_mode="Markdown",
        reply_markup=build_alerts_keyboard(alerts, lang)
    )

async def location_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /location [city] to set default city."""
    user = update.effective_user
    db_user = await get_or_create_user(user.id)
    lang = db_user.get("language", "bn")

    args = context.args
    query = " ".join(args).strip() if args else ""
    if not query:
        cur_loc = db_user.get("default_city") or "সেট করা নেই"
        await update.message.reply_text(
            f"🏠 **বর্তমান ডিফল্ট লোকেশন:** {cur_loc}\n\n"
            f"পরিবর্তন করতে শহরের নামসহ লিখুন।\n"
            f"যেমন: `/location Dhaka` বা `/location Chittagong`"
        )
        return

    cities = await search_city(query)
    if not cities:
        await update.message.reply_text(f"❌ '{query}' শহর খুঁজে পাওয়া যায়নি।")
        return

    city = cities[0]
    await set_default_location(user.id, city["name"], city["lat"], city["lon"])
    await update_alert_settings(user.id, city_name=city["name"], lat=city["lat"], lon=city["lon"])

    await update.message.reply_text(
        f"✅ আপনার ডিফল্ট ও অ্যালার্ট লোকেশন হিসেবে **{city['display_name']}** সেট করা হয়েছে!",
        parse_mode="Markdown"
    )

async def favorites_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /favorites to view and manage saved cities."""
    user = update.effective_user
    db_user = await get_or_create_user(user.id)
    lang = db_user.get("language", "bn")

    favs = await get_favorites(user.id)
    if not favs:
        await update.message.reply_text(
            "⭐ আপনার কোনো ফেভারিট লোকেশন সংরক্ষণ করা নেই।\n"
            "যেকোনো শহরের আবহাওয়া দেখে নিচের **'⭐ ফেভারিট সেভ'** বাটনে চাপ দিয়ে সংরক্ষণ করতে পারেন।"
        )
        return

    lines = ["⭐ **আপনার সংরক্ষিত প্রিয় স্থানসমূহ:**\n━━━━━━━━━━━━━━━━━━━━"]
    buttons = []
    for f in favs:
        lines.append(f"• **{f['city_name']}** (`/weather {f['city_name']}`)")
        buttons.append([
            InlineKeyboardButton(f"🌦️ {f['city_name']}", callback_data=f"ref:{f['lat']}:{f['lon']}:{f['city_name']}"),
            InlineKeyboardButton("❌ মুছুন", callback_data=f"delfav:{f['id']}")
        ])

    lines.append("━━━━━━━━━━━━━━━━━━━━\n💡 *আবহাওয়া দেখতে বা মুছে ফেলতে নিচের বাটন চাপুন:*")
    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def user_preferences_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries for settings, alerts, and favorites."""
    query = update.callback_query
    await query.answer()
    data = query.data
    user = update.effective_user

    # Settings toggle
    if data.startswith("cfg:"):
        _, setting_type, val = data.split(":")
        if setting_type == "lang":
            await update_user_setting(user.id, "language", val)
        elif setting_type == "unit":
            await update_user_setting(user.id, "temp_unit", val)

        # Refresh settings view
        db_user = await get_or_create_user(user.id)
        lang = db_user.get("language", "bn")
        unit = db_user.get("temp_unit", "C")
        def_city = db_user.get("default_city") or "Dhaka"
        msg = (
            f"⚙️ **ব্যক্তিগত সেটিংস (Personal Settings)**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🌐 **বর্তমান ভাষা:** {'বাংলা 🇧🇩' if lang == 'bn' else 'English 🇬🇧'}\n"
            f"🌡️ **তাপমাত্রার একক:** {'সেলসিয়াস (°C)' if unit == 'C' else 'ফারেনহাইট (°F)'}\n"
            f"🏠 **ডিফল্ট লোকেশন:** {def_city}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👇 *ভাষা ও একক পরিবর্তন করতে নিচের বাটনে চাপুন:*"
        )
        await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=build_settings_keyboard(lang, unit))
        await context.bot.send_message(chat_id=user.id, text="সেটিংস আপডেট হয়েছে ✅", reply_markup=get_main_keyboard(lang))

    # Alert toggles
    elif data.startswith("alt:"):
        _, alert_type = data.split(":")
        cur_alerts = await get_alert_settings(user.id)
        col_map = {
            "rain": "rain_alert",
            "severe": "severe_alert",
            "morning": "morning_report",
            "evening": "evening_report"
        }
        col = col_map.get(alert_type)
        if col:
            new_val = 0 if cur_alerts.get(col, 0) == 1 else 1
            await update_alert_settings(user.id, **{col: new_val})
            updated_alerts = await get_alert_settings(user.id)
            await query.edit_message_reply_markup(reply_markup=build_alerts_keyboard(updated_alerts))

    # Delete favorite
    elif data.startswith("delfav:"):
        fav_id = int(data.split(":")[1])
        await delete_favorite(user.id, fav_id)
        await query.answer("ফেভারিট লোকেশন মুছে ফেলা হয়েছে ✅", show_alert=True)
        # Update favorites list
        favs = await get_favorites(user.id)
        if not favs:
            await query.edit_message_text("⭐ আপনার তালিকায় আর কোনো প্রিয় স্থান সংরক্ষিত নেই।")
        else:
            lines = ["⭐ **আপনার সংরক্ষিত প্রিয় স্থানসমূহ:**\n━━━━━━━━━━━━━━━━━━━━"]
            buttons = []
            for f in favs:
                lines.append(f"• **{f['city_name']}** (`/weather {f['city_name']}`)")
                buttons.append([
                    InlineKeyboardButton(f"🌦️ {f['city_name']}", callback_data=f"ref:{f['lat']}:{f['lon']}:{f['city_name']}"),
                    InlineKeyboardButton("❌ মুছুন", callback_data=f"delfav:{f['id']}")
                ])
            lines.append("━━━━━━━━━━━━━━━━━━━━\n💡 *আবহাওয়া দেখতে বা মুছে ফেলতে নিচের বাটন চাপুন:*")
            await query.edit_message_text("\n".join(lines), parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))
