"""
Smart & Specialized Mode Handlers: /travel, /agriculture, /charts.
"""
from telegram import Update
from telegram.ext import ContextTypes
from database.db import get_or_create_user
from services.weather_api import search_city, get_weather_data
from services.travel import plan_travel
from services.agriculture import get_agriculture_advice
from services.charts import generate_weather_chart

async def travel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /travel [Origin to Destination]."""
    user = update.effective_user
    db_user = await get_or_create_user(user.id)
    lang = db_user.get("language", "bn")

    raw_args = " ".join(context.args).strip() if context.args else ""
    if not raw_args:
        help_msg = (
            "🧳 **ভ্রমণ আবহাওয়া প্ল্যানার ব্যবহার করার নিয়ম:**\n\n"
            "কমান্ডের সাথে যাত্রার স্থান এবং গন্তব্য লিখুন।\n"
            "উদাহরণ:\n"
            "👉 `/travel Dhaka to Cox's Bazar`\n"
            "👉 `/travel Dhaka -> Sylhet`\n"
            "👉 `/travel Chittagong to Sajek`"
            if lang == "bn" else
            "🧳 **How to use Travel Weather Planner:**\n\n"
            "Specify origin and destination.\n"
            "Example:\n"
            "👉 `/travel Dhaka to Cox's Bazar`\n"
            "👉 `/travel Dhaka -> Sylhet`"
        )
        await update.message.reply_text(help_msg, parse_mode="Markdown")
        return

    # Split on 'to' or '->'
    import re
    parts = re.split(r"\s+(?:to|থেকে|->|—>)\s+", raw_args, flags=re.IGNORECASE)
    if len(parts) < 2:
        await update.message.reply_text("⚠️ অনুগ্রহ করে 'to' বা '->' দিয়ে দুটি স্থান উল্লেখ করুন। যেমন: `/travel Dhaka to Cox's Bazar`")
        return

    origin, dest = parts[0].strip(), parts[1].strip()
    status_msg = await update.message.reply_text("🔍 ভ্রমণ রুটের আবহাওয়া বিশ্লেষণ করা হচ্ছে...")
    result = await plan_travel(origin, dest, lang)
    if not result:
        await status_msg.edit_text("❌ স্থানগুলোর আবহাওয়ার তথ্য খুঁজে পাওয়া যায়নি। অনুগ্রহ করে সঠিক ইংরেজি নাম লিখুন।")
        return

    await status_msg.edit_text(result, parse_mode="Markdown")

async def agriculture_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /agriculture [city]."""
    user = update.effective_user
    db_user = await get_or_create_user(user.id)
    lang = db_user.get("language", "bn")

    args = context.args
    query = " ".join(args).strip() if args else (db_user.get("default_city") or "Dhaka")

    cities = await search_city(query)
    if not cities:
        await update.message.reply_text(f"❌ '{query}' স্থান পাওয়া যায়নি।" if lang == "bn" else f"❌ Location '{query}' not found.")
        return

    city = cities[0]
    data = await get_weather_data(city["lat"], city["lon"])
    if not data:
        await update.message.reply_text("⚠️ কৃষি তথ্য লোড করা সম্ভব হয়নি।")
        return

    msg = get_agriculture_advice(data, city["display_name"], lang)
    await update.message.reply_text(msg, parse_mode="Markdown")

async def charts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /charts [city]."""
    user = update.effective_user
    db_user = await get_or_create_user(user.id)
    lang = db_user.get("language", "bn")

    args = context.args
    query = " ".join(args).strip() if args else (db_user.get("default_city") or "Dhaka")

    cities = await search_city(query)
    if not cities:
        await update.message.reply_text(f"❌ '{query}' শহর পাওয়া যায়নি।" if lang == "bn" else f"❌ City '{query}' not found.")
        return

    city = cities[0]
    data = await get_weather_data(city["lat"], city["lon"])
    if not data:
        await update.message.reply_text("⚠️ আবহাওয়া গ্রাফ তৈরি করা যায়নি।")
        return

    chart_buf = generate_weather_chart(data, city["name"], lang)
    if not chart_buf:
        await update.message.reply_text("⚠️ গ্রাফ তৈরি করতে সমস্যা হয়েছে।")
        return

    caption = f"📊 **{city['display_name']}** এর ২৪ ঘণ্টার তাপমাত্রা ও বৃষ্টির সম্ভাবনা গ্রাফ" if lang == "bn" else f"📊 24-hour weather visual analytics for **{city['display_name']}**"
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=chart_buf,
        caption=caption,
        parse_mode="Markdown"
    )
