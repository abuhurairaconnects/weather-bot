"""
Main Entry Point for the Telegram Weather Assistant Bot.
Initializes the database, configures handlers, and runs the bot with polling.
"""
import sys
import asyncio
import logging

# Ensure UTF-8 console encoding on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
from telegram import BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

from config import BOT_TOKEN
from database.db import init_db
from handlers.common import start_command, help_command, about_command
from handlers.weather_handler import weather_command, random_command, location_handler, weather_callback_dispatcher
from handlers.forecast_handler import forecast_command, hourly_command, advice_command
from handlers.division_handler import show_divisions_menu, division_callback_dispatcher
from handlers.conversation import handle_text_message

import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# Built-in lightweight HTTP health server to prevent Render/Cloud sleep
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        from config import GEMINI_API_KEY
        gemini_status = "Active ✅" if bool(GEMINI_API_KEY) else "Not Configured ⚠️"
        msg = f"🌦️ Telegram Weather Bot is Online & Active 24/7!\n🤖 Gemini AI: {gemini_status}\n📦 Version: 3.3.0-division-drilldown\n"
        self.wfile.write(msg.encode("utf-8"))

    def log_message(self, format, *args):
        # Silence ping log spamming
        pass

def run_health_server():
    port = int(os.getenv("PORT", 8080))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        logger.info(f"Keep-Alive Health Server running on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.warning(f"Could not bind health server on port {port}: {e}")

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log errors caused by updates."""
    logger.error("Exception while handling an update:", exc_info=context.error)

async def post_init(application):
    """Set up streamlined bot commands menu in Telegram."""
    commands = [
        BotCommand("start", "বট শুরু করুন / Start the bot"),
        BotCommand("division", "বিভাগ নির্বাচন / Browse by Division"),
        BotCommand("hourly", "২৪ ঘণ্টার পূর্বাভাস / 24-hour forecast"),
        BotCommand("forecast", "৭ দিনের পূর্বাভাস / 7-day forecast"),
        BotCommand("weather", "রিয়েল-টাইম আবহাওয়া / Real-time weather"),
        BotCommand("help", "কমান্ডের নির্দেশিকা / Help & commands"),
        BotCommand("about", "বট সম্পর্কে / About the bot")
    ]
    try:
        await application.bot.set_my_commands(commands)
        logger.info("Bot commands successfully registered with Telegram.")
    except Exception as e:
        logger.warning(f"Failed to register bot commands with Telegram: {e}")

def main():
    """Start and run the Telegram bot."""
    if not BOT_TOKEN or BOT_TOKEN == "your_bot_token_here":
        print("\n" + "=" * 60)
        print("❌ ERROR: TELEGRAM_BOT_TOKEN পাওয়া যায়নি!")
        print("অনুগ্রহ করে .env ফাইলে আপনার বট টোকেনটি যুক্ত করুন:")
        print("TELEGRAM_BOT_TOKEN=123456789:ABC-DEF...")
        print("টোকেন পেতে টেলিগ্রামে @BotFather-এ যান এবং /newbot লিখুন।")
        print("=" * 60 + "\n")
        sys.exit(1)

    # Initialize SQLite Database
    asyncio.run(init_db())
    print("✅ Database initialized successfully.")

    # Start Keep-Alive Health Server in background thread (keeps Render 24/7 active)
    threading.Thread(target=run_health_server, daemon=True).start()

    # Build Telegram Application
    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # 1. Common Commands
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))

    # 2. Division & Weather Commands
    application.add_handler(CommandHandler("division", show_divisions_menu))
    application.add_handler(CommandHandler("weather", weather_command))
    application.add_handler(CommandHandler("forecast", forecast_command))
    application.add_handler(CommandHandler("hourly", hourly_command))
    application.add_handler(CommandHandler("random", random_command))
    application.add_handler(CommandHandler("advice", advice_command))

    # 3. Hierarchical Division & Weather Button Callbacks
    application.add_handler(CallbackQueryHandler(division_callback_dispatcher, pattern=r"^(div|dist|dist_p|upz|back):"))
    application.add_handler(CallbackQueryHandler(weather_callback_dispatcher, pattern=r"^(ref|hr|fc|adv):"))

    # 4. Native Location Attachment
    application.add_handler(MessageHandler(filters.LOCATION, location_handler))

    # 5. Plain Text & Conversational Assistant
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    # Error handler
    application.add_error_handler(error_handler)

    print("🚀 Telegram Weather Assistant Bot চালু হচ্ছে...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
