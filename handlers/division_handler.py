"""
Division Handler:
Implements 3-tier hierarchical navigation for Bangladesh weather:
Division (৮টি বিভাগ) -> District (৬৪টি জেলা) -> Upazila (৪৯৫+ উপজেলা) -> Real-time Weather Card.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import math
from typing import Optional, Dict, Any, List

from database.db import get_or_create_user
from services.bd_geocoder import (
    get_all_divisions,
    get_districts_by_division,
    get_upazilas_by_district,
    find_bd_location,
    DISTRICT_NAME_CANONICAL
)
from services.weather_api import get_weather_data
from handlers.weather_handler import format_current_weather_card, format_lightning_alert_card
from config import is_authorized, ACCESS_DENIED_MESSAGE_BN

PAGE_SIZE = 10  # 10 upazilas per page (5 rows of 2 buttons)

def build_divisions_keyboard() -> InlineKeyboardMarkup:
    """Build inline keyboard showing all 8 divisions of Bangladesh in 2 columns."""
    divisions = get_all_divisions()
    buttons = []
    row = []
    for d in divisions:
        btn = InlineKeyboardButton(f"🏛️ {d['bn']}", callback_data=f"div:{d['en']}")
        row.append(btn)
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)

def build_districts_keyboard(division_en: str) -> InlineKeyboardMarkup:
    """Build inline keyboard showing all districts in the selected division."""
    districts = get_districts_by_division(division_en)
    buttons = []
    row = []
    for d in districts:
        btn = InlineKeyboardButton(d["name_bn"], callback_data=f"dist:{d['name_en']}")
        row.append(btn)
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    # Back button to division list
    buttons.append([InlineKeyboardButton("🔙 বিভাগ তালিকায় ফিরুন", callback_data="back:div")])
    return InlineKeyboardMarkup(buttons)

def build_upazilas_keyboard(district_en: str, page: int = 0) -> InlineKeyboardMarkup:
    """Build paginated inline keyboard for upazilas in the selected district."""
    canon_dist = DISTRICT_NAME_CANONICAL.get(district_en.lower(), district_en)
    upazilas = get_upazilas_by_district(canon_dist)
    total = len(upazilas)
    total_pages = max(1, math.ceil(total / PAGE_SIZE))
    page = max(0, min(page, total_pages - 1))

    start_idx = page * PAGE_SIZE
    end_idx = min(start_idx + PAGE_SIZE, total)
    page_upazilas = upazilas[start_idx:end_idx]

    buttons = []
    row = []
    for u in page_upazilas:
        btn = InlineKeyboardButton(u["name_bn"], callback_data=f"upz:{u['name_en']}")
        row.append(btn)
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    # Pagination controls if more than 1 page
    if total_pages > 1:
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton("◀️ পূর্ববর্তী", callback_data=f"dist_p:{canon_dist}:{page-1}"))
        else:
            nav_row.append(InlineKeyboardButton("•", callback_data="noop"))

        nav_row.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))

        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton("পরবর্তী ▶️", callback_data=f"dist_p:{canon_dist}:{page+1}"))
        else:
            nav_row.append(InlineKeyboardButton("•", callback_data="noop"))
        buttons.append(nav_row)

    # Back to district list button
    div_en = page_upazilas[0]["division_en"] if page_upazilas else "Dhaka"
    buttons.append([InlineKeyboardButton("🔙 জেলা তালিকায় ফিরুন", callback_data=f"back:dist:{div_en}")])
    return InlineKeyboardMarkup(buttons)

def build_upazila_weather_buttons(lat: float, lon: float, city_name: str, district_en: str, lang: str = "bn") -> InlineKeyboardMarkup:
    """Build action buttons for an upazila weather card."""
    row1 = [
        InlineKeyboardButton("📆 ২৪ ঘণ্টা" if lang == "bn" else "📆 24h", callback_data=f"hr:{lat:.4f}:{lon:.4f}:{city_name}"),
        InlineKeyboardButton("📅 ৭ দিন" if lang == "bn" else "📅 7 Days", callback_data=f"fc:{lat:.4f}:{lon:.4f}:{city_name}")
    ]
    row2 = [
        InlineKeyboardButton("🔄 রিফ্রেশ" if lang == "bn" else "🔄 Refresh", callback_data=f"ref:{lat:.4f}:{lon:.4f}:{city_name}"),
        InlineKeyboardButton("🔙 উপজেলা তালিকা", callback_data=f"back:upz:{district_en}")
    ]
    return InlineKeyboardMarkup([row1, row2])

async def show_divisions_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point: Displays the 8 administrative divisions of Bangladesh."""
    user = update.effective_user
    if not is_authorized(user.id):
        if update.message:
            await update.message.reply_text(ACCESS_DENIED_MESSAGE_BN, parse_mode="Markdown")
        elif update.callback_query:
            await update.callback_query.answer("⛔ অ্যাক্সেস সীমাবদ্ধ! আপনি এই বটের অনুমোদিত অ্যাডমিন নন।", show_alert=True)
        return

    text = (
        "🇧🇩 **বাংলাদেশ আবহাওয়া নেভিগেশন**\n"
        "──────────────────────\n"
        "অনুগ্রহ করে আপনার কাঙ্ক্ষিত **বিভাগ** নির্বাচন করুন:"
    )
    markup = build_divisions_keyboard()

    if update.callback_query:
        await update.callback_query.answer()
        try:
            await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=markup)
        except Exception:
            await update.callback_query.message.reply_text(text, parse_mode="Markdown", reply_markup=markup)
    elif update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=markup)

def build_lightning_divisions_keyboard() -> InlineKeyboardMarkup:
    """Build inline keyboard showing all 8 divisions for lightning alert drilldown."""
    divisions = get_all_divisions()
    buttons = []
    row = []
    for d in divisions:
        btn = InlineKeyboardButton(f"⚡ {d['bn']}", callback_data=f"ldiv:{d['en']}")
        row.append(btn)
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)

def build_lightning_districts_keyboard(division_en: str) -> InlineKeyboardMarkup:
    """Build inline keyboard showing all districts for lightning alert drilldown."""
    districts = get_districts_by_division(division_en)
    buttons = []
    row = []
    for d in districts:
        btn = InlineKeyboardButton(f"⛈️ {d['name_bn']}", callback_data=f"ldist:{d['name_en']}")
        row.append(btn)
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton("🔙 বিভাগ তালিকায় ফিরুন", callback_data="lback:div")])
    return InlineKeyboardMarkup(buttons)

def build_lightning_upazilas_keyboard(district_en: str, page: int = 0) -> InlineKeyboardMarkup:
    """Build paginated inline keyboard for upazilas for lightning alert drilldown."""
    canon_dist = DISTRICT_NAME_CANONICAL.get(district_en.lower(), district_en)
    upazilas = get_upazilas_by_district(canon_dist)
    total = len(upazilas)
    total_pages = max(1, math.ceil(total / PAGE_SIZE))
    page = max(0, min(page, total_pages - 1))

    start_idx = page * PAGE_SIZE
    end_idx = min(start_idx + PAGE_SIZE, total)
    page_upazilas = upazilas[start_idx:end_idx]

    buttons = []
    row = []
    for u in page_upazilas:
        btn = InlineKeyboardButton(f"⚡ {u['name_bn']}", callback_data=f"lupz:{u['name_en']}")
        row.append(btn)
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    # Pagination controls if more than 1 page
    if total_pages > 1:
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton("◀️ পূর্ববর্তী", callback_data=f"ldist_p:{canon_dist}:{page-1}"))
        else:
            nav_row.append(InlineKeyboardButton("•", callback_data="noop"))

        nav_row.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))

        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton("পরবর্তী ▶️", callback_data=f"ldist_p:{canon_dist}:{page+1}"))
        else:
            nav_row.append(InlineKeyboardButton("•", callback_data="noop"))
        buttons.append(nav_row)

    div_en = page_upazilas[0]["division_en"] if page_upazilas else "Dhaka"
    buttons.append([InlineKeyboardButton("🔙 জেলা তালিকায় ফিরুন", callback_data=f"lback:dist:{div_en}")])
    return InlineKeyboardMarkup(buttons)

def build_upazila_lightning_buttons(lat: float, lon: float, city_name: str, district_en: str, lang: str = "bn") -> InlineKeyboardMarkup:
    """Build action buttons for an upazila lightning card."""
    row1 = [
        InlineKeyboardButton("🔄 রিফ্রেশ" if lang == "bn" else "🔄 Refresh", callback_data=f"lref:{lat:.4f}:{lon:.4f}:{city_name}"),
        InlineKeyboardButton("🔙 উপজেলা তালিকা" if lang == "bn" else "🔙 Upazilas", callback_data=f"lback:upz:{district_en}")
    ]
    row2 = [
        InlineKeyboardButton("📆 ২৪ ঘণ্টা" if lang == "bn" else "📆 24h", callback_data=f"hr:{lat:.4f}:{lon:.4f}:{city_name}"),
        InlineKeyboardButton("🌦️ পূর্ণ আবহাওয়া" if lang == "bn" else "🌦️ Weather Card", callback_data=f"ref:{lat:.4f}:{lon:.4f}:{city_name}")
    ]
    return InlineKeyboardMarkup([row1, row2])

async def show_lightning_divisions_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point: Displays 8 divisions for lightning alert drilldown."""
    user = update.effective_user
    if not is_authorized(user.id):
        if update.message:
            await update.message.reply_text(ACCESS_DENIED_MESSAGE_BN, parse_mode="Markdown")
        elif update.callback_query:
            await update.callback_query.answer("⛔ অ্যাক্সেস সীমাবদ্ধ! আপনি এই বটের অনুমোদিত অ্যাডমিন নন।", show_alert=True)
        return

    text = (
        "⚡ **বজ্রপাত ও ঝড় সতর্কতা — বিভাগ নির্বাচন**\n"
        "──────────────────────\n"
        "আপনার এলাকার সুনির্দিষ্ট বজ্রপাত ঝুঁকি, কালবৈশাখী ঝড় ও বৃষ্টির আগাম সতর্কবার্তা জানতে নিচের তালিকা থেকে **বিভাগ** নির্বাচন করুন:"
    )
    markup = build_lightning_divisions_keyboard()

    if update.callback_query:
        await update.callback_query.answer()
        try:
            await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=markup)
        except Exception:
            await update.callback_query.message.reply_text(text, parse_mode="Markdown", reply_markup=markup)
    elif update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=markup)

async def safe_edit_callback_message(query, text: str, markup: Optional[InlineKeyboardMarkup] = None):
    """Safely edit callback message without throwing if text is identical or edit fails."""
    try:
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=markup)
    except Exception as e:
        if "Message is not modified" in str(e):
            return
        try:
            await query.message.reply_text(text, parse_mode="Markdown", reply_markup=markup)
        except Exception:
            pass

async def division_callback_dispatcher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles callbacks for division, district, and upazila navigation."""
    query = update.callback_query
    user = update.effective_user
    if not is_authorized(user.id):
        await query.answer("⛔ অ্যাক্সেস সীমাবদ্ধ! আপনি এই বটের অনুমোদিত অ্যাডমিন নন।", show_alert=True)
        return

    await query.answer()

    data = query.data
    if data == "noop":
        return

    # 1. Back to division list
    if data == "back:div":
        text = (
            "🇧🇩 **বাংলাদেশ আবহাওয়া নেভিগেশন**\n"
            "──────────────────────\n"
            "অনুগ্রহ করে আপনার কাঙ্ক্ষিত **বিভাগ** নির্বাচন করুন:"
        )
        await safe_edit_callback_message(query, text, build_divisions_keyboard())
        return

    # 2. Division clicked -> Show districts
    if data.startswith("div:") or data.startswith("back:dist:"):
        division_en = data.split(":", 1)[1] if data.startswith("div:") else data.split(":", 2)[2]
        div_info = next((d for d in get_all_divisions() if d["en"].lower() == division_en.lower()), None)
        div_bn = div_info["bn"] if div_info else division_en

        text = (
            f"🏛️ **{div_bn} বিভাগ**\n"
            f"──────────────────────\n"
            f"আপনার কাঙ্ক্ষিত **জেলা** নির্বাচন করুন:"
        )
        markup = build_districts_keyboard(division_en)
        await safe_edit_callback_message(query, text, markup)
        return

    # 3. District clicked -> Show upazilas (page 0)
    if data.startswith("dist:") or data.startswith("back:upz:"):
        district_en = data.split(":", 1)[1] if data.startswith("dist:") else data.split(":", 2)[2]
        canon_dist = DISTRICT_NAME_CANONICAL.get(district_en.lower(), district_en)
        upazilas = get_upazilas_by_district(canon_dist)
        dist_bn = upazilas[0]["district_bn"] if upazilas else canon_dist

        text = (
            f"📍 **{dist_bn} জেলা** (মোট {len(upazilas)}টি উপজেলা)\n"
            f"──────────────────────\n"
            f"আপনার কাঙ্ক্ষিত **উপজেলা** নির্বাচন করুন:"
        )
        markup = build_upazilas_keyboard(canon_dist, page=0)
        await safe_edit_callback_message(query, text, markup)
        return

    # 4. Upazila pagination (dist_p:<district_en>:<page>)
    if data.startswith("dist_p:"):
        parts = data.split(":")
        district_en = parts[1]
        page = int(parts[2])
        canon_dist = DISTRICT_NAME_CANONICAL.get(district_en.lower(), district_en)
        upazilas = get_upazilas_by_district(canon_dist)
        dist_bn = upazilas[0]["district_bn"] if upazilas else canon_dist

        text = (
            f"📍 **{dist_bn} জেলা** (মোট {len(upazilas)}টি উপজেলা)\n"
            f"──────────────────────\n"
            f"আপনার কাঙ্ক্ষিত **উপজেলা** নির্বাচন করুন:"
        )
        markup = build_upazilas_keyboard(canon_dist, page=page)
        await safe_edit_callback_message(query, text, markup)
        return

    # 5. Upazila clicked -> Show complete real-time weather card
    if data.startswith("upz:"):
        upazila_en = data.split(":", 1)[1]
        loc = find_bd_location(upazila_en)
        if not loc:
            await safe_edit_callback_message(query, f"⚠️ '{upazila_en}' এর তথ্য পাওয়া যায়নি।")
            return

        user = update.effective_user
        db_user = await get_or_create_user(user.id)
        lang = db_user.get("language", "bn")
        unit = db_user.get("temp_unit", "C")

        weather_data = await get_weather_data(loc["lat"], loc["lon"], unit)
        if not weather_data:
            await safe_edit_callback_message(query, "⚠️ আবহাওয়ার তথ্য লোড করা যায়নি। অনুগ্রহ করে কিছুক্ষণ পর আবার চেষ্টা করুন।")
            return

        card = format_current_weather_card(weather_data, loc["display_name"], lang, unit)
        markup = build_upazila_weather_buttons(
            loc["lat"],
            loc["lon"],
            loc["name"],
            loc.get("district") or loc.get("name"),
            lang
        )
        await safe_edit_callback_message(query, card, markup)
        return

    # 6. Lightning: Back to division list
    if data == "lback:div":
        text = (
            "⚡ **বজ্রপাত ও ঝড় সতর্কতা — বিভাগ নির্বাচন**\n"
            "──────────────────────\n"
            "আপনার এলাকার সুনির্দিষ্ট বজ্রপাত ঝুঁকি, কালবৈশাখী ঝড় ও বৃষ্টির আগাম সতর্কবার্তা জানতে নিচের তালিকা থেকে **বিভাগ** নির্বাচন করুন:"
        )
        await safe_edit_callback_message(query, text, build_lightning_divisions_keyboard())
        return

    # 7. Lightning: Division clicked or Back to district list -> Show districts
    if data.startswith("ldiv:") or data.startswith("lback:dist:"):
        division_en = data.split(":", 1)[1] if data.startswith("ldiv:") else data.split(":", 2)[2]
        div_info = next((d for d in get_all_divisions() if d["en"].lower() == division_en.lower()), None)
        div_bn = div_info["bn"] if div_info else division_en

        text = (
            f"⚡ **{div_bn} বিভাগ — জেলা নির্বাচন**\n"
            f"──────────────────────\n"
            f"বজ্রপাত সতর্কতা দেখতে আপনার কাঙ্ক্ষিত **জেলা** নির্বাচন করুন:"
        )
        markup = build_lightning_districts_keyboard(division_en)
        await safe_edit_callback_message(query, text, markup)
        return

    # 8. Lightning: District clicked or Back to upazila list -> Show upazilas (page 0)
    if data.startswith("ldist:") or data.startswith("lback:upz:"):
        district_en = data.split(":", 1)[1] if data.startswith("ldist:") else data.split(":", 2)[2]
        canon_dist = DISTRICT_NAME_CANONICAL.get(district_en.lower(), district_en)
        upazilas = get_upazilas_by_district(canon_dist)
        dist_bn = upazilas[0]["district_bn"] if upazilas else canon_dist

        text = (
            f"⛈️ **{dist_bn} জেলা — উপজেলা নির্বাচন** (মোট {len(upazilas)}টি উপজেলা)\n"
            f"──────────────────────\n"
            f"সুনির্দিষ্ট এলাকার বজ্রপাত ঝুঁকি ও সতর্কবার্তা দেখতে **উপজেলা** নির্বাচন করুন:"
        )
        markup = build_lightning_upazilas_keyboard(canon_dist, page=0)
        await safe_edit_callback_message(query, text, markup)
        return

    # 9. Lightning: Upazila pagination (ldist_p:<district_en>:<page>)
    if data.startswith("ldist_p:"):
        parts = data.split(":")
        district_en = parts[1]
        page = int(parts[2])
        canon_dist = DISTRICT_NAME_CANONICAL.get(district_en.lower(), district_en)
        upazilas = get_upazilas_by_district(canon_dist)
        dist_bn = upazilas[0]["district_bn"] if upazilas else canon_dist

        text = (
            f"⛈️ **{dist_bn} জেলা — উপজেলা নির্বাচন** (মোট {len(upazilas)}টি উপজেলা)\n"
            f"──────────────────────\n"
            f"সুনির্দিষ্ট এলাকার বজ্রপাত ঝুঁকি ও সতর্কবার্তা দেখতে **উপজেলা** নির্বাচন করুন:"
        )
        markup = build_lightning_upazilas_keyboard(canon_dist, page=page)
        await safe_edit_callback_message(query, text, markup)
        return

    # 10. Lightning: Upazila clicked -> Show dedicated lightning alert card
    if data.startswith("lupz:"):
        upazila_en = data.split(":", 1)[1]
        loc = find_bd_location(upazila_en)
        if not loc:
            await safe_edit_callback_message(query, f"⚠️ '{upazila_en}' এর তথ্য পাওয়া যায়নি।")
            return

        user = update.effective_user
        db_user = await get_or_create_user(user.id)
        lang = db_user.get("language", "bn")
        unit = db_user.get("temp_unit", "C")

        weather_data = await get_weather_data(loc["lat"], loc["lon"], unit)
        if not weather_data:
            await safe_edit_callback_message(query, "⚠️ আবহাওয়া তথ্য লোড করা যায়নি। অনুগ্রহ করে কিছুক্ষণ পর আবার চেষ্টা করুন।")
            return

        card = format_lightning_alert_card(weather_data, loc["display_name"], lang, unit)
        markup = build_upazila_lightning_buttons(
            loc["lat"],
            loc["lon"],
            loc["name"],
            loc.get("district") or loc.get("name"),
            lang
        )
        await safe_edit_callback_message(query, card, markup)
        return

    # 11. Lightning: Refresh button clicked (lref:<lat>:<lon>:<city_name>)
    if data.startswith("lref:"):
        parts = data.split(":")
        lat = float(parts[1])
        lon = float(parts[2])
        city_name = parts[3]

        user = update.effective_user
        db_user = await get_or_create_user(user.id)
        lang = db_user.get("language", "bn")
        unit = db_user.get("temp_unit", "C")

        from services.weather_api import invalidate_weather_cache
        invalidate_weather_cache(lat, lon)

        weather_data = await get_weather_data(lat, lon, unit)
        if not weather_data:
            await query.answer("⚠️ রিফ্রেশ ব্যর্থ হয়েছে!", show_alert=True)
            return

        loc = find_bd_location(city_name)
        display_name = loc["display_name"] if loc else city_name
        district_en = (loc.get("district") if loc else None) or city_name

        card = format_lightning_alert_card(weather_data, display_name, lang, unit)
        markup = build_upazila_lightning_buttons(lat, lon, city_name, district_en, lang)
        await safe_edit_callback_message(query, card, markup)
        await query.answer("✅ তথ্য সফলভাবে আপডেট হয়েছে!")
        return