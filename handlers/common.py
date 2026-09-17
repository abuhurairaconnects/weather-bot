"""
Common Handlers: /start, /help, /about, and terminology explanations.
"""
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from database.db import get_or_create_user
from utils.i18n import TERMINOLOGY_EXPLANATIONS

def get_main_keyboard(lang: str = "bn") -> ReplyKeyboardMarkup:
    """Return persistent reply keyboard with only Division, 24h, and 7-day forecast buttons."""
    if lang == "bn":
        keyboard = [
            ["🏢 বিভাগ"],
            ["📆 ২৪ ঘণ্টার পূর্বাভাস", "📅 ৭ দিনের পূর্বাভাস"]
        ]
    else:
        keyboard = [
            ["🏢 Divisions"],
            ["📆 24-Hour Forecast", "📅 7-Day Forecast"]
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
            "আমি আপনাকে বাংলাদেশের যেকোনো বিভাগ, জেলা ও উপজেলার নিখুঁত রিয়েল-টাইম আবহাওয়া ও পূর্বাভাস জানাতে প্রস্তুত।\n\n"
            "📌 **ব্যবহারের নির্দেশিকা:**\n"
            "• **🏢 বিভাগ:** নিচের বাটনে চাপ দিয়ে বিভাগ ➡️ জেলা ➡️ উপজেলা সিলেক্ট করে আবহাওয়া দেখুন।\n"
            "• **সরাসরি অনুসন্ধান:** যেকোনো জেলা বা উপজেলার নাম লিখুন (যেমন: `বরুড়া`, `কুষ্টিয়া`, `মিরপুর`, `তাড়াশ`)।\n"
            "• **পূর্বাভাস:** নিচের কীবোর্ড থেকে **২৪ ঘণ্টার পূর্বাভাস** ও **৭ দিনের পূর্বাভাস** দেখুন।\n\n"
            "💡 সব কমান্ড দেখতে /help চাপুন।"
        )
    else:
        msg = (
            "👋 **Assalamu Alaikum, I am Abu Huraira's AI Assistant, how can I help you?** 🌦️\n\n"
            "I provide real-time weather and forecasts for any division, district, and upazila in Bangladesh.\n\n"
            "📌 **Quick Guide:**\n"
            "• **🏢 Divisions:** Tap the button to navigate Division ➡️ District ➡️ Upazila.\n"
            "• **Direct Search:** Type any district or upazila name (e.g., `Barura`, `Kushtia`, `Mirpur`).\n"
            "• **Forecasts:** Use buttons below for **24-Hour Forecast** and **7-Day Forecast**.\n\n"
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
            "🌦️ **প্রধান ফিচারসমূহ:**\n"
            "• `/division` — ৮টি বিভাগ, জেলা ও উপজেলা অনুযায়ী আবহাওয়া নির্বাচন\n"
            "• `/weather [স্থান]` — যেকোনো জেলা বা উপজেলার রিয়েল-টাইম আবহাওয়া\n"
            "• `/hourly [স্থান]` — পরবর্তী ২৪ ঘণ্টার প্রতি ঘণ্টার তথ্য\n"
            "• `/forecast [স্থান]` — আগামী ৭ দিনের পূর্বাভাস\n\n"
            "📍 **নেভিগেশন:**\n"
            "• নিচের **🏢 বিভাগ** বাটনে চাপ দিয়ে ক্রমান্বয়ে বিভাগ ➡️ জেলা ➡️ উপজেলা সিলেক্ট করুন।\n"
            "• অথবা সরাসরি যেকোনো জেলা/উপজেলার নাম লিখুন।"
        )
    else:
        help_text = (
            "📖 **Bot Commands & User Guide**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🌦️ **Core Weather Features:**\n"
            "• `/division` — Hierarchical Division ➡️ District ➡️ Upazila navigation\n"
            "• `/weather [area]` — Current real-time weather\n"
            "• `/hourly [area]` — Next 24 hours hourly forecast\n"
            "• `/forecast [area]` — Next 7 days extended forecast\n\n"
            "📍 **Quick Tips:**\n"
            "• Use the **🏢 Divisions** button below to browse by location.\n"
            "• Or simply send any district or upazila name directly."
        )

    await update.message.reply_text(help_text, parse_mode="Markdown", reply_markup=get_main_keyboard(lang))

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
