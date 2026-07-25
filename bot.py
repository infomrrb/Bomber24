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
# SMS বট কনফিগ
SMS_BOT_TOKEN = "8072096171:AAF0UBOlXnyQNBjczNeeFVDCaiExja1xiF0"
SMS_API_URL = "https://api.paglahost.shop/Custom_SMS/api.php"
SMS_API_KEY = "Shuvo55356"

# BOMBER বট কনফিগ
BOMBER_TOKEN = "8578238506:AAHHZpeEJAdT9iND8aal-x13PPrN-9H_miw"
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
            total_sms INTEGER DEFAULT 0
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
            reply_markup=get_admin_keyboard()
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
            reply_markup=get_back_keyboard()
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

# ===================== এসএমএস সেন্ড (পুরনো বট) =====================
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
    context.user_data['sms_step'] = 'number'

# ===================== SMS BOMBER (দ্বিতীয় বট) =====================
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
        reply_markup=get_back_keyboard()
    )
    context.user_data['bomber_step'] = 'number'

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
        if 'sms_step' in context.user_data:
            del context.user_data['sms_step']
        if 'bomber_step' in context.user_data:
            del context.user_data['bomber_step']
        return
    
    # ===== SMS সেন্ড প্রসেস =====
    if 'sms_step' in context.user_data:
        await process_sms(update, context)
        return
    
    # ===== BOMBER প্রসেস =====
    if 'bomber_step' in context.user_data:
        await process_bomber(update, context)
        return
    
    # ===== রিডিম প্রসেস =====
    if 'redeem_step' in context.user_data:
        await process_redeem(update, context)
        return
    
    await update.message.reply_text(
        "❌ Invalid command!\nUse the buttons below.",
        reply_markup=get_main_keyboard()
    )

# ===================== এসএমএস প্রসেস =====================
async def process_sms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """SMS প্রসেসিং"""
    user_id = update.effective_user.id
    message = update.message.text
    step = context.user_data.get('sms_step')
    
    if step == 'number':
        # নম্বর ভ্যালিডেশন
        if not message.isdigit() or len(message) < 11:
            await update.message.reply_text("❌ Invalid number! Try again:")
            return
        
        context.user_data['sms_number'] = message
        context.user_data['sms_step'] = 'message'
        
        await update.message.reply_text(
            f"✅ Number set: {message}\n\n"
            f"💬 Enter your message:",
            reply_markup=get_back_keyboard()
        )
    
    elif step == 'message':
        number = context.user_data['sms_number']
        sms_text = message
        
        await update.message.reply_text(f"⏳ Sending SMS to {number}...")
        
        # API কল
        params = {
            "key": SMS_API_KEY,
            "number": number,
            "msg": sms_text
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(SMS_API_URL, params=params) as resp:
                    data = await resp.json()
                    
                    if data.get("status") == "success":
                        # ক্রেডিট ডিডাক্ট
                        async with aiosqlite.connect("unified_bot.db") as db:
                            await db.execute("UPDATE users SET balance = balance - 1 WHERE user_id = ?", (user_id,))
                            await db.execute("UPDATE users SET total_sms = total_sms + 1 WHERE user_id = ?", (user_id,))
                            await db.commit()
                        
                        await update.message.reply_text(
                            f"✅ SMS Sent Successfully!\n"
                            f"💰 1 Credit deducted.\n\n"
                            f"📩 Reply: {data.get('message', 'Success')}",
                            reply_markup=get_main_keyboard()
                        )
                    else:
                        await update.message.reply_text(
                            f"❌ Failed to send SMS!\n"
                            f"⚠️ {data.get('message', 'Unknown error')}",
                            reply_markup=get_main_keyboard()
                        )
        except Exception as e:
            await update.message.reply_text(
                f"❌ Error: {str(e)}",
                reply_markup=get_main_keyboard()
            )
        
        # ক্লিয়ার
        del context.user_data['sms_step']
        del context.user_data['sms_number']

# ===================== BOMBER প্রসেস =====================
async def process_bomber(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bomber প্রসেসিং"""
    user_id = update.effective_user.id
    message = update.message.text
    step = context.user_data.get('bomber_step')
    
    if step == 'number':
        if not message.isdigit() or len(message) < 11:
            await update.message.reply_text("❌ Invalid number! Try again:")
            return
        
        context.user_data['bomber_number'] = message
        context.user_data['bomber_step'] = 'amount'
        
        await update.message.reply_text(
            f"✅ Number set: {message}\n\n"
            f"💥 Enter amount (1-100):",
            reply_markup=get_back_keyboard()
        )
    
    elif step == 'amount':
        try:
            amount = int(message)
            if amount < 1 or amount > 100:
                await update.message.reply_text("❌ Amount must be 1-100!")
                return
            
            number = context.user_data['bomber_number']
            
            msg = await update.message.reply_text(
                f"⏳ Bombing in progress...\n"
                f"📱 Target: {number}\n"
                f"💥 Amount: {amount}"
            )
            
            success_count = 0
            
            for i in range(amount):
                try:
                    response = requests.get(f"{BOMBER_API_URL}{number}", timeout=10)
                    data = response.json()
                    
                    if data.get('success', 0) > 0:
                        success_count += data.get('success', 0)
                    
                    # প্রগ্রেস আপডেট
                    if (i + 1) % 5 == 0 or (i + 1) == amount:
                        await msg.edit_text(
                            f"⏳ Bombing...\n"
                            f"📱 Target: {number}\n"
                            f"✅ Success: {success_count}\n"
                            f"📊 Progress: {i+1}/{amount}"
                        )
                    
                    time.sleep(0.3)
                    
                except Exception as e:
                    logger.error(f"Bomber API Error: {e}")
            
            # ডাটাবেস আপডেট
            async with aiosqlite.connect("unified_bot.db") as db:
                await db.execute(
                    "UPDATE users SET total_bombing = total_bombing + 1 WHERE user_id = ?",
                    (user_id,)
                )
                await db.commit()
            
            await msg.edit_text(
                f"✅ Bombing Complete!\n\n"
                f"📱 Target: {number}\n"
                f"💥 Amount: {amount}\n"
                f"✅ Success: {success_count}\n"
                f"📊 Success Rate: {round((success_count/amount)*100, 2)}%",
                reply_markup=get_main_keyboard()
            )
            
            # ক্লিয়ার
            del context.user_data['bomber_step']
            del context.user_data['bomber_number']
            
        except ValueError:
            await update.message.reply_text("❌ Invalid amount! Enter a number:")

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
                    f"👤 Username: {row[0]}\n"
                    f"💰 Credits: {row[1]}\n"
                    f"🚦 Status: {row[2].capitalize()}\n"
                    f"📨 SMS Sent: {row[3]}\n"
                    f"💣 Bombing: {row[4]}\n\n"
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
            "SELECT total_sms, total_bombing FROM users WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            
            if row:
                await update.message.reply_text(
                    f"📊 **My Stats**\n\n"
                    f"📨 Total SMS Sent: {row[0]}\n"
                    f"💣 Total Bombing: {row[1]}\n\n"
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
    context.user_data['redeem_step'] = 'code'

async def process_redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """রিডিম প্রসেস"""
    user_id = update.effective_user.id
    code = update.message.text.strip()
    
    async with aiosqlite.connect("unified_bot.db") as db:
        # চেক করা ইউজার আগে ব্যবহার করেছে কিনা
        async with db.execute("SELECT 1 FROM redeem_history WHERE user_id = ? AND code = ?", (user_id, code)) as cur:
            if await cur.fetchone():
                await update.message.reply_text("❌ You already used this code!")
                del context.user_data['redeem_step']
                return
        
        # কোড ভ্যালিডেশন
        async with db.execute("SELECT amount, usages FROM redeem_codes WHERE code = ?", (code,)) as cur:
            row = await cur.fetchone()
            if not row or row[1] <= 0:
                await update.message.reply_text("❌ Invalid or expired code!")
                del context.user_data['redeem_step']
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
    del context.user_data['redeem_step']

# ===================== অ্যাডমিন কমান্ড =====================
async def handle_admin_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """অ্যাডমিন কমান্ড হ্যান্ডল"""
    # এখানে আপনার পুরনো অ্যাডমিন ফাংশনগুলো যোগ করুন
    pass

# ===================== মেইন =====================
async def main():
    """বট চালু"""
    await init_db()
    
    application = Application.builder().token(SMS_BOT_TOKEN).build()
    
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
