"""
Common Handlers: /start, /help, /about, and terminology explanations.
"""
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from database.db import get_or_create_user
from utils.i18n import TERMINOLOGY_EXPLANATIONS

def get_main_keyboard(lang: str = "bn") -> ReplyKeyboardMarkup:
    """Return persistent reply keyboard with quick actions."""
    if lang == "bn":
        keyboard = [
            [KeyboardButton("📍 আমার লাইভ লোকেশন শেয়ার করুন", request_location=True)],
            ["🌦️ ঢাকা আবহাওয়া", "📊 গ্রাফ চার্ট"],
            ["📆 ২৪ ঘণ্টা পূর্বাভাস", "📅 ৭ দিনের পূর্বাভাস"],
            ["🧠 স্মার্ট পরামর্শ", "🌾 কৃষি মোড"],
            ["🌫️ এয়ার কোয়ালিটি", "⚙️ সেটিংস ও অ্যালার্ট"]
        ]
    else:
        keyboard = [
            [KeyboardButton("📍 Share Live Location", request_location=True)],
            ["🌦️ Dhaka Weather", "📊 Weather Chart"],
            ["📆 24h Hourly Forecast", "📅 7-Day Forecast"],
            ["🧠 Smart Advice", "🌾 Agriculture Mode"],
            ["🌫️ Air Quality", "⚙️ Settings & Alerts"]
        ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    db_user = await get_or_create_user(user.id, user.username, user.first_name)
    lang = db_user.get("language", "bn")

    if lang == "bn":
        msg = (
            "👋 **আসসালামু আলাইকুম, আমি আবু হুরাইরার AI অ্যাসিস্ট্যান্ট, আপনাকে কীভাবে সাহায্য করি?** 🌦️\n\n"
            "আমি আপনাকে যেকোনো এলাকার রিয়েল-টাইম আবহাওয়া ও পূর্বাভাস জানাতে প্রস্তুত। এছাড়াও সাধারণ জ্ঞান, বিজ্ঞান, আড্ডা বা যেকোনো বিষয়ে আপনার প্রশ্নের উত্তর দিতে পারি।\n\n"
            "📌 **যেভাবে ব্যবহার করবেন:**\n"
            "• সরাসরি যেকোনো এলাকার নাম লিখুন (যেমন: `মিরপুর`, `কুষ্টিয়া`, `ফেনী`, `Dhaka`, `London`)\n"
            "• নিচের বাটন চেপে আপনার **লাইভ লোকেশন** শেয়ার করুন\n"
            "• অথবা যেকোনো প্রশ্ন লিখুন (যেমন: *\"কুষ্টিয়ার রিয়েল-টাইম ওয়েদার কেমন?\"*, *\"আজ কি বৃষ্টি হবে?\"*, *\"চাঁদ কেন আলো দেয়?\"*)\n\n"
            "💡 সব কমান্ড দেখতে /help চাপুন।"
        )
    else:
        msg = (
            "👋 **Assalamu Alaikum, I am Abu Huraira's AI Assistant, how can I help you?** 🌦️\n\n"
            "I provide hyper-local real-time weather conditions, forecasts, air quality, and can answer any general question you have.\n\n"
            "📌 **Quick Guide:**\n"
            "• Type any area or city name (e.g., `Mirpur`, `Kushtia`, `Dhaka`, `London`)\n"
            "• Tap the button below to **Share Live Location**\n"
            "• Or ask natural questions like *\"Will it rain today?\"* or *\"Tell me a fun fact\"*\n\n"
            "💡 Type /help to see all commands."
        )

    await update.message.reply_text(
        msg,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(lang)
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    user = update.effective_user
    db_user = await get_or_create_user(user.id)
    lang = db_user.get("language", "bn")

    if lang == "bn":
        help_text = (
            "📖 **বটের কমান্ড তালিকা ও ব্যবহারের নির্দেশিকা**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🌦️ **মৌলিক আবহাওয়া:**\n"
            "• `/weather [শহর]` — বর্তমান ১৬+ আবহাওয়া মেট্রিক্স\n"
            "• `/hourly [শহর]` — পরবর্তী ২৪ ঘণ্টার প্রতি ঘণ্টার তথ্য\n"
            "• `/forecast [শহর]` — ৭ থেকে ১০ দিনের পূর্বাভাস\n"
            "• `/rain [শহর]` — বৃষ্টির সম্ভাবনা ও বিস্তারিত হিসাব\n"
            "• `/airquality [শহর]` — বায়ুমান (AQI) ও স্বাস্থ্য সতর্কবার্তা\n\n"
            "🧠 **স্মার্ট ও স্পেশালাইজড ফিচার:**\n"
            "• `/charts [শহর]` — ২৪ ঘণ্টার তাপমাত্রা ও বৃষ্টির গ্রাফ ছবি\n"
            "• `/agriculture [শহর]` — কৃষকদের জন্য সেচ, স্প্রে ও ফসল শুকানোর বুলেটিন\n"
            "• `/travel [যাত্রা to গন্তব্য]` — ভ্রমণ আবহাওয়া ও প্যাকিং পরামর্শ\n"
            "  *(উদাহরণ: `/travel Dhaka to Cox's Bazar`)*\n\n"
            "⚙️ **প্রোফাইল, অ্যালার্ট ও সেটিংস:**\n"
            "• `/location [শহর]` — হোম/ডিফল্ট লোকেশন সেট করুন\n"
            "• `/favorites` — প্রিয় স্থানসমূহ সংরক্ষণ ও দ্রুত ভিউ\n"
            "• `/alerts` — বৃষ্টির অ্যালার্ট ও সকাল/সন্ধ্যার দৈনিক রিপোর্ট\n"
            "• `/settings` — ভাষা (বাংলা/English) ও ইউনিট (°C/°F)\n\n"
            "🤖 **প্রাকৃতিক প্রশ্ন:**\n"
            "আপনি সরাসরি যেকোনো প্রশ্ন লিখতে পারেন! যেমন:\n"
            "👉 *\"আজ কি বৃষ্টি হবে?\"*\n"
            "👉 *\"কাল সকালে বাইরে যাওয়া যাবে?\"*\n"
            "👉 *\"বাতাসের আর্দ্রতা কী?\"*"
        )
    else:
        help_text = (
            "📖 **Bot Commands & User Guide**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🌦️ **Weather & Forecasts:**\n"
            "• `/weather [city]` — Current weather (16+ metrics)\n"
            "• `/hourly [city]` — Next 24 hours detailed forecast\n"
            "• `/forecast [city]` — 7 to 10 days extended forecast\n"
            "• `/rain [city]` — Rain probability and precipitation\n"
            "• `/airquality [city]` — Air Quality Index (AQI) & safety tips\n\n"
            "🧠 **Smart & Specialized Modes:**\n"
            "• `/charts [city]` — 24h temperature and rain graph\n"
            "• `/agriculture [city]` — Farming, irrigation, and drying advice\n"
            "• `/travel [Origin to Dest]` — Travel weather and packing guide\n"
            "  *(e.g., `/travel Dhaka to Cox's Bazar`)*\n\n"
            "⚙️ **Settings & Alerts:**\n"
            "• `/location [city]` — Set your default/home location\n"
            "• `/favorites` — Save favorite cities for 1-click access\n"
            "• `/alerts` — Rain warnings & daily morning/evening briefs\n"
            "• `/settings` — Change language (EN/BN) and unit (°C/°F)\n\n"
            "🤖 **Conversational AI:**\n"
            "Simply send natural questions:\n"
            "👉 *\"Will it rain today?\"*\n"
            "👉 *\"Do I need an umbrella in Dhaka?\"*"
        )

    await update.message.reply_text(help_text, parse_mode="Markdown")

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /about command."""
    about_text = (
        "ℹ️ **About Weather Assistant Bot**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🌦️ **Version:** 3.0.0 (All-In-One Unified Edition)\n"
        "⚡ **Powered by:** Open-Meteo Global Forecasting & Air Quality API\n"
        "🛡️ **Privacy:** Completely secure, no personal data shared.\n"
        "✨ **Key Features:** 16+ Weather Metrics, 24h Charts, Rain Alerts, Agriculture Mode, Travel Route Planner, Natural Language Assistant."
    )
    await update.message.reply_text(about_text, parse_mode="Markdown")
