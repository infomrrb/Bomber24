import asyncio
import logging
import re
import time
import json
import requests
import aiosqlite
import aiohttp
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ===================== কনফিগারেশন =====================
# ইউনিফাইড টোকেন (একই টোকেন)
BOT_TOKEN = "8826486988:AAFOOfdcrVCgvj532plzOQUXwx40yn3USl0"

# SMS API কনফিগ (আপনার প্রথম বটের)
SMS_API_URL = "https://api.paglahost.shop/Custom_SMS/api.php"
SMS_API_KEY = "Shuvo55356"

# BOMBER API কনফিগ (আপনার দ্বিতীয় বটের)
BOMBER_API_URL = "https://apu-sand.vercel.app/send?number="

# কমন কনফিগ
ADMIN_ID = 1967494059
ADMIN_USERNAME = "@RobiEntertainment"
OWNER_USERNAME = "@DARK_TUSHAR"
CHANNEL_USERNAME = "@VOTER_LIST_BANGLADESH"
LOG_CHANNEL = -1001234567890

# ===================== লগিং =====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===================== ডাটাবেস =====================
async def init_db():
    async with aiosqlite.connect("unified_bot.db") as db:
        # ইউজার টেবিল
        await db.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance INTEGER DEFAULT 0,
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active',
            total_bombing INTEGER DEFAULT 0,
            total_sms INTEGER DEFAULT 0,
            total_success INTEGER DEFAULT 0,
            total_failed INTEGER DEFAULT 0
        )""")
        
        # অ্যাকাউন্ট টেবিল
        await db.execute("""CREATE TABLE IF NOT EXISTS accounts (
            username TEXT PRIMARY KEY,
            password TEXT,
            telegram_id INTEGER
        )""")
        
        # রিডিম কোড টেবিল
        await db.execute("""CREATE TABLE IF NOT EXISTS redeem_codes (
            code TEXT PRIMARY KEY,
            amount INTEGER,
            usages INTEGER
        )""")
        
        # রিডিম হিস্ট্রি
        await db.execute("""CREATE TABLE IF NOT EXISTS redeem_history (
            user_id INTEGER,
            code TEXT,
            PRIMARY KEY (user_id, code)
        )""")
        
        # অ্যাডমিন যোগ
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, balance, status) VALUES (?, 'Admin', 9999, 'active')",
            (ADMIN_ID,)
        )
        await db.commit()

# ===================== চেক ফাংশন =====================
async def is_channel_member(user_id, context):
    """চেক করে ইউজার চ্যানেলের মেম্বার কিনা"""
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

async def is_logged_in(user_id):
    """চেক করে ইউজার লগইন করেছে কিনা"""
    if user_id == ADMIN_ID:
        return True
    async with aiosqlite.connect("unified_bot.db") as db:
        async with db.execute("SELECT status FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row and row[0] == 'active'

# ===================== কীবোর্ড =====================
def get_main_keyboard():
    """মেইন মেনু কীবোর্ড"""
    keyboard = [
        ["📨 Send SMS", "💣 SMS Bomber"],
        ["👤 My Profile", "🎁 Redeem Code"],
        ["📊 My Stats", "📞 Contact Admin"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_admin_keyboard():
    """অ্যাডমিন কীবোর্ড"""
    keyboard = [
        ["➕ Add Credit", "➖ Remove Credit"],
        ["🚫 User Ban", "✅ User Unban"],
        ["📣 Broadcast", "🎟 Create Redeem Code"],
        ["👥 Total Users", "🔐 Create Account"],
        ["⬅️ Back to User"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_back_keyboard():
    """ব্যাক বাটন"""
    keyboard = [["🔙 Back"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ===================== স্টার্ট =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start কমান্ড"""
    user_id = update.effective_user.id
    
    # চ্যানেল চেক
    if not await is_channel_member(user_id, context):
        keyboard = [
            [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("✅ Check", callback_data='check_join')]
        ]
        await update.message.reply_text(
            f"⚠️ Please join our channel to use this bot!\n\n"
            f"🔗 Channel: {CHANNEL_USERNAME}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # অ্যাডমিন চেক
    if user_id == ADMIN_ID:
        await update.message.reply_text(
            "👑 **Admin Panel**\nWelcome back, Admin!",
            reply_markup=get_admin_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    # ইউজার চেক
    if await is_logged_in(user_id):
        await update.message.reply_text(
            f"🔥 Welcome to Unified SMS Bot!\n\n"
            f"👤 User: {update.effective_user.first_name}\n"
            f"🆔 ID: {user_id}\n\n"
            f"📌 Select an option:",
            reply_markup=get_main_keyboard()
        )
    else:
        await update.message.reply_text(
            "🔒 **Login Required**\n\nPlease contact admin for login credentials.",
            reply_markup=get_back_keyboard(),
            parse_mode='Markdown'
        )

# ===================== ক্যালব্যাক হ্যান্ডলার =====================
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """বাটন ক্লিক হ্যান্ডলার"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if query.data == 'check_join':
        if await is_channel_member(user_id, context):
            await query.message.delete()
            await context.bot.send_message(
                chat_id=user_id,
                text="✅ Thanks for joining!\n\n🔥 Welcome to Unified SMS Bot!",
                reply_markup=get_main_keyboard()
            )
        else:
            await query.edit_message_text(
                f"❌ You haven't joined yet!\n\n"
                f"🔗 Channel: {CHANNEL_USERNAME}"
            )

# ===================== মেসেজ হ্যান্ডলার =====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """সব মেসেজ হ্যান্ডল করে"""
    user_id = update.effective_user.id
    message = update.message.text
    
    # চ্যানেল চেক
    if not await is_channel_member(user_id, context):
        keyboard = [
            [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("✅ Check", callback_data='check_join')]
        ]
        await update.message.reply_text(
            f"⚠️ Please join our channel!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # ===== অ্যাডমিন কমান্ড =====
    if user_id == ADMIN_ID:
        await handle_admin_commands(update, context)
        return
    
    # ===== মেইন মেনু =====
    if message == "📨 Send SMS":
        await send_sms(update, context)
        return
    
    elif message == "💣 SMS Bomber":
        await sms_bomber(update, context)
        return
    
    elif message == "👤 My Profile":
        await show_profile(update, context)
        return
    
    elif message == "🎁 Redeem Code":
        await ask_redeem(update, context)
        return
    
    elif message == "📊 My Stats":
        await show_stats(update, context)
        return
    
    elif message == "📞 Contact Admin":
        await update.message.reply_text(
            f"📞 Contact Admin\n\n"
            f"👨‍💻 Admin: {ADMIN_USERNAME}\n"
            f"👨‍💻 Owner: {OWNER_USERNAME}",
            reply_markup=get_main_keyboard()
        )
        return
    
    elif message == "🔙 Back":
        await update.message.reply_text(
            "🏠 Main Menu",
            reply_markup=get_main_keyboard()
        )
        # ক্লিয়ার স্টেট
        context.user_data.clear()
        return
    
    # ===== স্টেট অনুযায়ী প্রসেস =====
    if context.user_data.get('state') == 'sms_number':
        await process_sms_number(update, context)
        return
    
    elif context.user_data.get('state') == 'sms_message':
        await process_sms_message(update, context)
        return
    
    elif context.user_data.get('state') == 'bomber_number':
        await process_bomber_number(update, context)
        return
    
    elif context.user_data.get('state') == 'bomber_amount':
        await process_bomber_amount(update, context)
        return
    
    elif context.user_data.get('state') == 'redeem_code':
        await process_redeem(update, context)
        return
    
    await update.message.reply_text(
        "❌ Invalid command!\nUse the buttons below.",
        reply_markup=get_main_keyboard()
    )

# ===================== এসএমএস সেন্ড =====================
async def send_sms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """SMS পাঠানোর ফাংশন"""
    user_id = update.effective_user.id
    
    if not await is_logged_in(user_id):
        await update.message.reply_text("❌ Please login first!")
        return
    
    # ব্যালেন্স চেক
    async with aiosqlite.connect("unified_bot.db") as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if not row or row[0] < 1:
                await update.message.reply_text(f"❌ Insufficient credits! Contact Admin: {ADMIN_USERNAME}")
                return
    
    await update.message.reply_text(
        "📱 Enter phone number (e.g., 018XXXXXXXX):",
        reply_markup=get_back_keyboard()
    )
    context.user_data['state'] = 'sms_number'

async def process_sms_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """SMS নম্বর প্রসেস"""
    number = update.message.text.strip()
    
    # ভ্যালিডেশন
    if not number.isdigit() or len(number) < 11:
        await update.message.reply_text("❌ Invalid number! Enter 11 digits (e.g., 018XXXXXXXX):")
        return
    
    context.user_data['sms_number'] = number
    context.user_data['state'] = 'sms_message'
    
    await update.message.reply_text(
        f"✅ Number: {number}\n\n"
        f"💬 Enter your message:",
        reply_markup=get_back_keyboard()
    )

async def process_sms_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """SMS মেসেজ প্রসেস"""
    user_id = update.effective_user.id
    number = context.user_data.get('sms_number')
    sms_text = update.message.text
    
    await update.message.reply_text(f"⏳ Sending SMS to {number}...")
    
    # API কল
    params = {
        "key": SMS_API_KEY,
        "number": number,
        "msg": sms_text
    }
    
    success = False
    api_response = ""
    
    try:
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(SMS_API_URL, params=params) as resp:
                raw_text = await resp.text()
                api_response = raw_text
                
                try:
                    json_data = await resp.json()
                    if json_data.get("status") == "success":
                        success = True
                        api_response = json_data.get("message", "Success")
                except:
                    if resp.status == 200 and "error" not in raw_text.lower():
                        success = True
                        api_response = raw_text
    except Exception as e:
        api_response = f"Error: {str(e)}"
    
    if success:
        async with aiosqlite.connect("unified_bot.db") as db:
            await db.execute("UPDATE users SET balance = balance - 1 WHERE user_id = ?", (user_id,))
            await db.execute("UPDATE users SET total_sms = total_sms + 1 WHERE user_id = ?", (user_id,))
            await db.commit()
        
        await update.message.reply_text(
            f"✅ SMS Sent Successfully!\n"
            f"💰 1 Credit deducted.\n\n"
            f"📩 Response: {api_response}",
            reply_markup=get_main_keyboard()
        )
    else:
        await update.message.reply_text(
            f"❌ Failed to send SMS!\n"
            f"⚠️ {api_response}",
            reply_markup=get_main_keyboard()
        )
    
    context.user_data.clear()

# ===================== SMS BOMBER =====================
async def sms_bomber(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """SMS Bomber ফাংশন"""
    user_id = update.effective_user.id
    
    if not await is_logged_in(user_id):
        await update.message.reply_text("❌ Please login first!")
        return
    
    await update.message.reply_text(
        "💣 **SMS BOMBER**\n\n"
        "Enter target number (e.g., 018XXXXXXXX):\n"
        "⚠️ Max 100 messages",
        reply_markup=get_back_keyboard(),
        parse_mode='Markdown'
    )
    context.user_data['state'] = 'bomber_number'

async def process_bomber_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bomber নম্বর প্রসেস"""
    number = update.message.text.strip()
    
    if not number.isdigit() or len(number) < 11:
        await update.message.reply_text("❌ Invalid number! Enter 11 digits (e.g., 018XXXXXXXX):")
        return
    
    context.user_data['bomber_number'] = number
    context.user_data['state'] = 'bomber_amount'
    
    await update.message.reply_text(
        f"✅ Number: {number}\n\n"
        f"💥 Enter amount (1-100):",
        reply_markup=get_back_keyboard()
    )

async def process_bomber_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bomber অ্যামাউন্ট প্রসেস"""
    user_id = update.effective_user.id
    number = context.user_data.get('bomber_number')
    
    try:
        amount = int(update.message.text.strip())
        if amount < 1 or amount > 100:
            await update.message.reply_text("❌ Amount must be between 1-100!")
            return
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number!")
        return
    
    # প্রক্রেসিং মেসেজ
    msg = await update.message.reply_text(
        f"⏳ Bombing in progress...\n\n"
        f"📱 Target: {number}\n"
        f"💥 Amount: {amount}\n"
        f"⏰ Please wait..."
    )
    
    success_count = 0
    failed_count = 0
    
    for i in range(amount):
        try:
            # সিঙ্ক্রোনাস রিকোয়েস্ট (telegram বটের জন্য)
            response = requests.get(f"{BOMBER_API_URL}{number}", timeout=10)
            data = response.json()
            
            # সাফল্য গণনা
            if data.get('success', 0) > 0:
                success_count += data.get('success', 0)
            else:
                failed_count += 1
                
        except Exception as e:
            failed_count += 1
            logger.error(f"Bomber API Error: {e}")
        
        # প্রতি ৫টি রিকোয়েস্টে আপডেট
        if (i + 1) % 5 == 0 or (i + 1) == amount:
            try:
                await msg.edit_text(
                    f"⏳ Bombing in progress...\n\n"
                    f"📱 Target: {number}\n"
                    f"✅ Success: {success_count}\n"
                    f"❌ Failed: {failed_count}\n"
                    f"📊 Progress: {i+1}/{amount}"
                )
            except:
                pass
        
        # ছোট ডিলে
        time.sleep(0.3)
    
    # ডাটাবেস আপডেট
    async with aiosqlite.connect("unified_bot.db") as db:
        await db.execute(
            "UPDATE users SET total_bombing = total_bombing + 1 WHERE user_id = ?",
            (user_id,)
        )
        await db.execute(
            "UPDATE users SET total_success = total_success + ? WHERE user_id = ?",
            (success_count, user_id)
        )
        await db.execute(
            "UPDATE users SET total_failed = total_failed + ? WHERE user_id = ?",
            (failed_count, user_id)
        )
        await db.commit()
    
    # সফলতার হার
    success_rate = round((success_count / amount) * 100, 2) if amount > 0 else 0
    
    # রেসাল্ট
    result_message = (
        f"✅ Bombing Complete! ✅\n\n"
        f"📱 Target: {number}\n"
        f"💥 Amount: {amount}\n"
        f"✅ Success: {success_count}\n"
        f"❌ Failed: {failed_count}\n"
        f"📊 Success Rate: {success_rate}%\n\n"
        f"👨‍💻 API Owner: DARK_TUSHAR"
    )
    
    await msg.edit_text(result_message, reply_markup=get_main_keyboard())
    context.user_data.clear()

# ===================== প্রোফাইল =====================
async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """প্রোফাইল দেখায়"""
    user_id = update.effective_user.id
    
    async with aiosqlite.connect("unified_bot.db") as db:
        async with db.execute(
            "SELECT username, balance, status, total_sms, total_bombing FROM users WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            
            if row:
                await update.message.reply_text(
                    f"👤 **My Profile**\n\n"
                    f"🆔 ID: `{user_id}`\n"
                    f"👤 Username: {row[0] or 'N/A'}\n"
                    f"💰 Credits: {row[1]}\n"
                    f"🚦 Status: {row[2].capitalize()}\n"
                    f"📨 SMS Sent: {row[3]}\n"
                    f"💣 Bombing Done: {row[4]}\n\n"
                    f"👨‍💻 Admin: {ADMIN_USERNAME}",
                    parse_mode="Markdown",
                    reply_markup=get_main_keyboard()
                )

# ===================== স্ট্যাটস =====================
async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """স্ট্যাটস দেখায়"""
    user_id = update.effective_user.id
    
    async with aiosqlite.connect("unified_bot.db") as db:
        async with db.execute(
            "SELECT total_sms, total_bombing, total_success, total_failed FROM users WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            
            if row:
                total_requests = row[2] + row[3]
                success_rate = round((row[2] / total_requests) * 100, 2) if total_requests > 0 else 0
                
                await update.message.reply_text(
                    f"📊 **My Stats**\n\n"
                    f"📨 Total SMS Sent: {row[0]}\n"
                    f"💣 Total Bombing: {row[1]}\n"
                    f"✅ Total Success: {row[2]}\n"
                    f"❌ Total Failed: {row[3]}\n"
                    f"📊 Success Rate: {success_rate}%\n\n"
                    f"📌 Use 'Send SMS' or 'SMS Bomber' to increase stats!",
                    parse_mode="Markdown",
                    reply_markup=get_main_keyboard()
                )

# ===================== রিডিম =====================
async def ask_redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """রিডিম কোড চায়"""
    await update.message.reply_text(
        "🎟 Enter Redeem Code:",
        reply_markup=get_back_keyboard()
    )
    context.user_data['state'] = 'redeem_code'

async def process_redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """রিডিম প্রসেস"""
    user_id = update.effective_user.id
    code = update.message.text.strip()
    
    async with aiosqlite.connect("unified_bot.db") as db:
        # চেক করা ইউজার আগে ব্যবহার করেছে কিনা
        async with db.execute("SELECT 1 FROM redeem_history WHERE user_id = ? AND code = ?", (user_id, code)) as cur:
            if await cur.fetchone():
                await update.message.reply_text("❌ You already used this code!")
                context.user_data.clear()
                return
        
        # কোড ভ্যালিডেশন
        async with db.execute("SELECT amount, usages FROM redeem_codes WHERE code = ?", (code,)) as cur:
            row = await cur.fetchone()
            if not row or row[1] <= 0:
                await update.message.reply_text("❌ Invalid or expired code!")
                context.user_data.clear()
                return
            
            amount = row[0]
            
            # ক্রেডিট যোগ
            await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
            await db.execute("UPDATE redeem_codes SET usages = usages - 1 WHERE code = ?", (code,))
            await db.execute("INSERT INTO redeem_history (user_id, code) VALUES (?, ?)", (user_id, code))
            await db.commit()
    
    await update.message.reply_text(
        f"🎉 Code Redeemed!\n✅ You got +{amount} Credits!",
        reply_markup=get_main_keyboard()
    )
    context.user_data.clear()

# ===================== অ্যাডমিন কমান্ড =====================
async def handle_admin_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """অ্যাডমিন কমান্ড হ্যান্ডল"""
    message = update.message.text
    
    if message == "⬅️ Back to User":
        await update.message.reply_text(
            "Switched to User Mode.",
            reply_markup=get_main_keyboard()
        )
        return
    
    elif message == "👥 Total Users":
        async with aiosqlite.connect("unified_bot.db") as db:
            async with db.execute("SELECT COUNT(*) FROM users") as cur:
                total = await cur.fetchone()
            async with db.execute("SELECT COUNT(*) FROM accounts") as cur:
                accounts = await cur.fetchone()
        
        await update.message.reply_text(
            f"📊 **System Stats**\n\n"
            f"👥 Total Users: {total[0]}\n"
            f"🔐 Accounts: {accounts[0]}",
            parse_mode='Markdown'
        )
        return
    
    elif message == "➕ Add Credit":
        await update.message.reply_text("👤 Enter Telegram ID:")
        context.user_data['admin_state'] = 'add_id'
        return
    
    elif message == "➖ Remove Credit":
        await update.message.reply_text("👤 Enter Telegram ID:")
        context.user_data['admin_state'] = 'remove_id'
        return
    
    elif message == "🚫 User Ban":
        await update.message.reply_text("👤 Enter Telegram ID to BAN:")
        context.user_data['admin_state'] = 'ban_id'
        return
    
    elif message == "✅ User Unban":
        await update.message.reply_text("👤 Enter Telegram ID to UNBAN:")
        context.user_data['admin_state'] = 'unban_id'
        return
    
    elif message == "📣 Broadcast":
        await update.message.reply_text("📢 Send broadcast message:")
        context.user_data['admin_state'] = 'broadcast'
        return
    
    elif message == "🎟 Create Redeem Code":
        await update.message.reply_text("🎟 Enter code name (e.g., FREE50):")
        context.user_data['admin_state'] = 'code_name'
        return
    
    elif message == "🔐 Create Account":
        await update.message.reply_text("👤 Enter username:")
        context.user_data['admin_state'] = 'acc_user'
        return
    
    # অ্যাডমিন স্টেট প্রসেস
    if context.user_data.get('admin_state'):
        await process_admin_states(update, context)

async def process_admin_states(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """অ্যাডমিন স্টেট প্রসেস"""
    user_id = update.effective_user.id
    message = update.message.text
    state = context.user_data.get('admin_state')
    
    if state == 'add_id':
        try:
            target_id = int(message)
            context.user_data['target_id'] = target_id
            context.user_data['admin_state'] = 'add_amount'
            await update.message.reply_text("💰 Enter amount:")
        except ValueError:
            await update.message.reply_text("❌ Invalid ID! Enter a number.")
            context.user_data['admin_state'] = None
    
    elif state == 'add_amount':
        try:
            amount = int(message)
            target_id = context.user_data.get('target_id')
            
            async with aiosqlite.connect("unified_bot.db") as db:
                await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, target_id))
                await db.commit()
            
            await update.message.reply_text(f"✅ Added {amount} credits to user {target_id}.")
            context.user_data['admin_state'] = None
        except ValueError:
            await update.message.reply_text("❌ Invalid amount!")
            context.user_data['admin_state'] = None
    
    elif state == 'remove_id':
        try:
            target_id = int(message)
            context.user_data['target_id'] = target_id
            context.user_data['admin_state'] = 'remove_amount'
            await update.message.reply_text("💰 Enter amount to remove:")
        except ValueError:
            await update.message.reply_text("❌ Invalid ID!")
            context.user_data['admin_state'] = None
    
    elif state == 'remove_amount':
        try:
            amount = int(message)
            target_id = context.user_data.get('target_id')
            
            async with aiosqlite.connect("unified_bot.db") as db:
                await db.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, target_id))
                await db.commit()
            
            await update.message.reply_text(f"✅ Removed {amount} credits from user {target_id}.")
            context.user_data['admin_state'] = None
        except ValueError:
            await update.message.reply_text("❌ Invalid amount!")
            context.user_data['admin_state'] = None
    
    elif state == 'ban_id':
        try:
            target_id = int(message)
            async with aiosqlite.connect("unified_bot.db") as db:
                await db.execute("UPDATE users SET status = 'banned' WHERE user_id = ?", (target_id,))
                await db.commit()
            await update.message.reply_text(f"🚫 User {target_id} banned!")
            context.user_data['admin_state'] = None
        except ValueError:
            await update.message.reply_text("❌ Invalid ID!")
            context.user_data['admin_state'] = None
    
    elif state == 'unban_id':
        try:
            target_id = int(message)
            async with aiosqlite.connect("unified_bot.db") as db:
                await db.execute("UPDATE users SET status = 'active' WHERE user_id = ?", (target_id,))
                await db.commit()
            await update.message.reply_text(f"✅ User {target_id} unbanned!")
            context.user_data['admin_state'] = None
        except ValueError:
            await update.message.reply_text("❌ Invalid ID!")
            context.user_data['admin_state'] = None
    
    elif state == 'broadcast':
        broadcast_text = message
        
        async with aiosqlite.connect("unified_bot.db") as db:
            async with db.execute("SELECT user_id FROM users") as cur:
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
        
        await update.message.reply_text(f"✅ Sent to {success} users.")
        context.user_data['admin_state'] = None
    
    elif state == 'code_name':
        code = message.strip()
        context.user_data['code_name'] = code
        context.user_data['admin_state'] = 'code_amount'
        await update.message.reply_text("💰 Enter amount:")
    
    elif state == 'code_amount':
        try:
            amount = int(message)
            context.user_data['code_amount'] = amount
            context.user_data['admin_state'] = 'code_usages'
            await update.message.reply_text("👥 Enter number of uses:")
        except ValueError:
            await update.message.reply_text("❌ Invalid amount!")
            context.user_data['admin_state'] = None
    
    elif state == 'code_usages':
        try:
            usages = int(message)
            code = context.user_data.get('code_name')
            amount = context.user_data.get('code_amount')
            
            async with aiosqlite.connect("unified_bot.db") as db:
                await db.execute(
                    "INSERT INTO redeem_codes (code, amount, usages) VALUES (?, ?, ?)",
                    (code, amount, usages)
                )
                await db.commit()
            
            await update.message.reply_text(
                f"✅ Code Created!\n"
                f"🎟 Code: `{code}`\n"
                f"💰 Amount: {amount}\n"
                f"👥 Uses: {usages}",
                parse_mode='Markdown'
            )
            context.user_data['admin_state'] = None
        except ValueError:
            await update.message.reply_text("❌ Invalid number!")
            context.user_data['admin_state'] = None
    
    elif state == 'acc_user':
        username = message.strip()
        context.user_data['acc_user'] = username
        context.user_data['admin_state'] = 'acc_pass'
        await update.message.reply_text("🔑 Enter password:")
    
    elif state == 'acc_pass':
        password = message.strip()
        username = context.user_data.get('acc_user')
        
        async with aiosqlite.connect("unified_bot.db") as db:
            try:
                await db.execute(
                    "INSERT INTO accounts (username, password) VALUES (?, ?)",
                    (username, password)
                )
                await db.commit()
                await update.message.reply_text(
                    f"✅ Account Created!\n"
                    f"👤 Username: `{username}`\n"
                    f"🔑 Password: `{password}`",
                    parse_mode='Markdown'
                )
            except aiosqlite.IntegrityError:
                await update.message.reply_text("❌ Username already exists!")
        
        context.user_data['admin_state'] = None

# ===================== মেইন =====================
async def main():
    """বট চালু"""
    await init_db()
    
    # নতুন টোকেন দিয়ে বট চালু
    application = Application.builder().token(BOT_TOKEN).build()
    
    # হ্যান্ডলার
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("="*50)
    print("🤖 Unified SMS Bot চালু হচ্ছে...")
    print("📢 Channel:", CHANNEL_USERNAME)
    print("👨‍💻 Admin:", ADMIN_USERNAME)
    print("✅ বট সম্পূর্ণ রেডি!")
    print("="*50)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    asyncio.run(main())
