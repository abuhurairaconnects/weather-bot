"""
Common Handlers: /start, /help, /about, and terminology explanations.
"""
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from database.db import get_or_create_user
from utils.i18n import TERMINOLOGY_EXPLANATIONS

def get_main_keyboard(lang: str = "bn") -> ReplyKeyboardMarkup:
    """Return persistent reply keyboard with core quick actions."""
    if lang == "bn":
        keyboard = [
            [KeyboardButton("📍 আমার লাইভ লোকেশন শেয়ার করুন", request_location=True)],
            ["🌦️ লাইভ আবহাওয়া", "📆 ২৪ ঘণ্টা পূর্বাভাস"],
            ["📅 ৭ দিনের পূর্বাভাস", "🧠 স্মার্ট পরামর্শ"]
        ]
    else:
        keyboard = [
            [KeyboardButton("📍 Share Live Location", request_location=True)],
            ["🌦️ Live Weather", "📆 24h Hourly Forecast"],
            ["📅 7-Day Forecast", "🧠 Smart Advice"]
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
            "আমি আপনাকে যেকোনো জেলা ও উপজেলার রিয়েল-টাইম আবহাওয়া ও পূর্বাভাস জানাতে প্রস্তুত। এছাড়াও সাধারণ জ্ঞান, বিজ্ঞান, আড্ডা বা যেকোনো বিষয়ে আপনার প্রশ্নের উত্তর দিতে পারি।\n\n"
            "📌 **যেভাবে ব্যবহার করবেন:**\n"
            "• সরাসরি যেকোনো জেলা বা উপজেলার নাম লিখুন (যেমন: `মিরপুর`, `কুষ্টিয়া`, `ভেড়ামারা`, `দিনাজপুর`)\n"
            "• নিচের বাটন চেপে আপনার **লাইভ লোকেশন** শেয়ার করুন\n"
            "• অথবা নিচের কীবোর্ড থেকে ২৪ ঘণ্টার বা ৭ দিনের পূর্বাভাস ও স্মার্ট পরামর্শ দেখুন\n"
            "• যেকোনো সাধারণ প্রশ্নের উত্তর জানতে সরাসরি বাংলায় লিখুন\n\n"
            "💡 সব কমান্ড দেখতে /help চাপুন।"
        )
    else:
        msg = (
            "👋 **Assalamu Alaikum, I am Abu Huraira's AI Assistant, how can I help you?** 🌦️\n\n"
            "I provide real-time weather conditions for any district or upazila, 24h & 7-day forecasts, smart advice, and can answer any general questions.\n\n"
            "📌 **Quick Guide:**\n"
            "• Type any district, upazila, or area name (e.g., `Mirpur`, `Kushtia`, `Dhaka`)\n"
            "• Tap the button below to **Share Live Location**\n"
            "• Or explore 24h hourly, 7-day forecast, and smart advice\n"
            "• Ask any general questions freely\n\n"
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
            "🌦️ **প্রধান আবহাওয়া ফিচারসমূহ:**\n"
            "• `/weather [জেলা/উপজেলা]` — বর্তমান রিয়েল-টাইম আবহাওয়া\n"
            "• `/hourly [জেলা/উপজেলা]` — পরবর্তী ২৪ ঘণ্টার প্রতি ঘণ্টার তথ্য\n"
            "• `/forecast [জেলা/উপজেলা]` — আগামী ৭ দিনের পূর্বাভাস\n"
            "• `/advice [জেলা/উপজেলা]` — স্মার্ট পরামর্শ (ছাতা, পোশাক, আউটডোর)\n\n"
            "📍 **যেকোনো জেলা বা উপজেলা:**\n"
            "• সরাসরি যেকোনো জেলা বা উপজেলার নাম বাংলায় বা ইংরেজিতে লিখুন (যেমন: `মিরপুর`, `কুষ্টিয়া`, `ভেড়ামারা`, `দিনাজপুর`)\n"
            "• অথবা নিচের বাটন চেপে আপনার **লাইভ লোকেশন** শেয়ার করুন\n\n"
            "🤖 **আবু হুরাইরার AI অ্যাসিস্ট্যান্ট:**\n"
            "আবহাওয়া ছাড়াও যেকোনো বিষয়ে সরাসরি প্রশ্ন করতে পারেন:\n"
            "👉 *\"আজ কি বৃষ্টি হবে?\"*\n"
            "👉 *\"আজকের সর্বোচ্চ তাপমাত্রা কত?\"*\n"
            "👉 *\"সূর্য কেন আলো দেয়?\"*"
        )
    else:
        help_text = (
            "📖 **Bot Commands & User Guide**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🌦️ **Core Weather Features:**\n"
            "• `/weather [area]` — Current real-time weather\n"
            "• `/hourly [area]` — Next 24 hours hourly forecast\n"
            "• `/forecast [area]` — Next 7 days extended forecast\n"
            "• `/advice [area]` — Smart lifestyle advice (umbrella, clothing)\n\n"
            "📍 **Any District or Upazila:**\n"
            "• Simply type any district or upazila name to get instant weather\n"
            "• Or tap **Share Live Location**\n\n"
            "🤖 **Abu Huraira's AI Assistant:**\n"
            "Ask any question freely beyond weather:\n"
            "👉 *\"Will it rain today?\"*\n"
            "👉 *\"Do I need an umbrella?\"*"
        )

    await update.message.reply_text(help_text, parse_mode="Markdown")

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /about command."""
    about_text = (
        "ℹ️ **About Weather Assistant Bot**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🌦️ **Version:** 3.1.0 (Streamlined AI Assistant Edition)\n"
        "⚡ **Powered by:** Open-Meteo Global Forecasting API & Google Gemini AI\n"
        "🤖 **Developer:** Abu Huraira\n"
        "🛡️ **Privacy:** Completely secure, no personal data shared.\n"
        "✨ **Core Features:** Real-Time District/Upazila Weather, 24h Forecast, 7-Day Forecast, Smart Advice & AI Assistant."
    )
    await update.message.reply_text(about_text, parse_mode="Markdown")
