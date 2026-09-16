"""
Admin Dashboard & Broadcast Handlers.
Restricted to ADMIN_IDS configured in config.py or .env.
"""
from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_IDS
from database.db import get_admin_stats, get_all_user_ids, update_user_setting

def is_admin(user_id: int) -> bool:
    """Verify if user is in admin list. If ADMIN_IDS is empty, allow first user or warn."""
    return (not ADMIN_IDS) or (user_id in ADMIN_IDS)

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin dashboard view."""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("⛔ আপনার এই কমান্ড ব্যবহারের অনুমতি নেই।")
        return

    stats = await get_admin_stats()
    top_locs_str = "\n".join([f"  • {name}: {count} বার" for name, count in stats["top_locations"]]) or "  • কোনো রেকর্ড নেই"

    dashboard = (
        f"🛠️ **অ্যাডমিন কন্ট্রোল প্যানেল (Admin Dashboard)**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 **মোট ইউজার:** {stats['total_users']} জন\n"
        f"🚫 **ব্লকড ইউজার:** {stats['blocked_users']} জন\n"
        f"🔔 **অ্যাক্টিভ অ্যালার্ট গ্রাহক:** {stats['active_alerts']} জন\n\n"
        f"📍 **সর্বাধিক সার্চ হওয়া শহরসমূহ:**\n{top_locs_str}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📢 **ব্রডকাস্ট করার নিয়ম:**\n"
        f"`/broadcast আপনার মেসেজ এখানে লিখুন`\n\n"
        f"🚫 **ইউজার ব্লক করার নিয়ম:**\n"
        f"`/block <user_id>` বা `/unblock <user_id>`"
    )
    await update.message.reply_text(dashboard, parse_mode="Markdown")

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast an announcement message to all registered users."""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("⛔ আপনার এই কমান্ড ব্যবহারের অনুমতি নেই।")
        return

    broadcast_text = " ".join(context.args).strip() if context.args else ""
    if not broadcast_text:
        await update.message.reply_text("⚠️ অনুগ্রহ করে মেসেজটি লিখুন। যেমন: `/broadcast সার্ভার মেইনটেন্যান্স চলবে...`")
        return

    user_ids = await get_all_user_ids()
    sent_count = 0
    failed_count = 0

    status_msg = await update.message.reply_text(f"📤 {len(user_ids)} জন ইউজারের কাছে মেসেজ পাঠানো শুরু হচ্ছে...")

    announcement = f"📢 **অফিসিয়াল নোটিশ (Weather Bot Update):**\n\n{broadcast_text}"
    for uid in user_ids:
        try:
            await context.bot.send_message(chat_id=uid, text=announcement, parse_mode="Markdown")
            sent_count += 1
        except Exception:
            failed_count += 1

    await status_msg.edit_text(
        f"✅ **ব্রডকাস্ট সম্পন্ন হয়েছে!**\n\n"
        f"• সফলভাবে প্রেরিত: {sent_count}\n"
        f"• ব্যর্থ/ব্লক করেছে: {failed_count}"
    )

async def block_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Block a user from using the bot."""
    user = update.effective_user
    if not is_admin(user.id):
        return

    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("ব্যবহার: `/block <user_id>`")
        return

    target_id = int(context.args[0])
    await update_user_setting(target_id, "is_blocked", 1)
    await update.message.reply_text(f"🚫 ইউজার `{target_id}` ব্লক করা হয়েছে।")

async def unblock_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unblock a user."""
    user = update.effective_user
    if not is_admin(user.id):
        return

    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("ব্যবহার: `/unblock <user_id>`")
        return

    target_id = int(context.args[0])
    await update_user_setting(target_id, "is_blocked", 0)
    await update.message.reply_text(f"✅ ইউজার `{target_id}` আনব্লক করা হয়েছে।")
