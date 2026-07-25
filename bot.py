import asyncio
import logging
import requests
import aiosqlite
import aiohttp
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ===================== কনফিগারেশন =====================
BOT_TOKEN = "8826486988:AAFOOfdcrVCgvj532plzOQUXwx40yn3USl0"
ADMIN_ID = 1967494059
ADMIN_USERNAME = "@RobiEntertainment"
OWNER_USERNAME = "@RobiEntertainment"
CHANNEL_USERNAME = "@VOTER_LIST_BANGLADESH"

# SMS API
SMS_API_URL = "https://api.paglahost.shop/Custom_SMS/api.php"
SMS_API_KEY = "Shuvo55356"

# BOMBER API
BOMBER_API_URL = "https://apu-sand.vercel.app/send?number="

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
            
            # অ্যাডমিন যোগ
            await db.execute(
                "INSERT OR IGNORE INTO users (user_id, username, balance, status) VALUES (?, 'Admin', 9999, 'active')",
                (ADMIN_ID,)
            )
            await db.commit()
            logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"Database error: {e}")

# ===================== চেক ফাংশন =====================
async def is_admin(user_id):
    """চেক করে ইউজার অ্যাডমিন কিনা"""
    return user_id == ADMIN_ID

# ===================== কীবোর্ড =====================
def get_main_keyboard():
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
        ["📊 User Stats"],
        ["⬅️ Back to User"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_back_keyboard():
    keyboard = [["🔙 Back"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ===================== /start =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """স্টার্ট কমান্ড"""
    user = update.effective_user
    user_id = user.id
    
    logger.info(f"Start command from user: {user_id}")
    
    # অ্যাডমিন চেক
    if await is_admin(user_id):
        await update.message.reply_text(
            f"👑 **Admin Panel**\n\n"
            f"🔥 Welcome Admin {user.first_name}!\n"
            f"🆔 ID: {user_id}\n\n"
            f"📌 Select an option:",
            parse_mode="Markdown",
            reply_markup=get_admin_keyboard()
        )
        return
    
    await update.message.reply_text(
        f"🔥 Welcome {user.first_name}!\n\n"
        f"🆔 ID: {user_id}\n\n"
        f"📌 Select an option:",
        reply_markup=get_main_keyboard()
    )

# ===================== মেসেজ হ্যান্ডলার =====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """সব মেসেজ হ্যান্ডল করে"""
    user_id = update.effective_user.id
    message = update.message.text
    
    logger.info(f"Message from {user_id}: {message}")
    
    # ===== অ্যাডমিন কমান্ড =====
    if await is_admin(user_id):
        await handle_admin_commands(update, context)
        return
    
    # ===== ব্যাক বাটন =====
    if message == "🔙 Back":
        await update.message.reply_text(
            "🏠 Main Menu",
            reply_markup=get_main_keyboard()
        )
        context.user_data.clear()
        return
    
    # ===== Send SMS =====
    if message == "📨 Send SMS":
        await update.message.reply_text(
            "📱 Enter phone number (e.g., 018XXXXXXXX):",
            reply_markup=get_back_keyboard()
        )
        context.user_data['state'] = 'sms_number'
        return
    
    # ===== SMS Bomber =====
    if message == "💣 SMS Bomber":
        await update.message.reply_text(
            "💣 Enter target number (e.g., 018XXXXXXXX):",
            reply_markup=get_back_keyboard()
        )
        context.user_data['state'] = 'bomber_number'
        return
    
    # ===== My Profile =====
    if message == "👤 My Profile":
        await show_profile(update, context)
        return
    
    # ===== Redeem Code =====
    if message == "🎁 Redeem Code":
        await update.message.reply_text(
            "🎟 Enter redeem code:",
            reply_markup=get_back_keyboard()
        )
        context.user_data['state'] = 'redeem_code'
        return
    
    # ===== My Stats =====
    if message == "📊 My Stats":
        await show_stats(update, context)
        return
    
    # ===== Contact Admin =====
    if message == "📞 Contact Admin":
        await update.message.reply_text(
            f"📞 Contact Admin\n\n"
            f"👨‍💻 Admin: {ADMIN_USERNAME}\n"
            f"👨‍💻 Owner: {OWNER_USERNAME}",
            reply_markup=get_main_keyboard()
        )
        return
    
    # ===== স্টেট অনুযায়ী প্রসেস =====
    state = context.user_data.get('state')
    
    if state == 'sms_number':
        await process_sms_number(update, context)
    elif state == 'sms_message':
        await process_sms_message(update, context)
    elif state == 'bomber_number':
        await process_bomber_number(update, context)
    elif state == 'bomber_amount':
        await process_bomber_amount(update, context)
    elif state == 'redeem_code':
        await process_redeem(update, context)
    else:
        await update.message.reply_text(
            "❌ Please use the buttons below:",
            reply_markup=get_main_keyboard()
        )

# ===================== অ্যাডমিন কমান্ড =====================
async def handle_admin_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """অ্যাডমিন কমান্ড হ্যান্ডল"""
    message = update.message.text
    
    # ===== ব্যাক টু ইউজার =====
    if message == "⬅️ Back to User":
        await update.message.reply_text(
            "🔄 Switched to User Mode",
            reply_markup=get_main_keyboard()
        )
        context.user_data.clear()
        return
    
    # ===== টোটাল ইউজার =====
    if message == "👥 Total Users":
        async with aiosqlite.connect("bot_database.db") as db:
            async with db.execute("SELECT COUNT(*) FROM users") as cur:
                total = await cur.fetchone()
            async with db.execute("SELECT COUNT(*) FROM accounts") as cur:
                accounts = await cur.fetchone()
            async with db.execute("SELECT COUNT(*) FROM users WHERE status = 'active'") as cur:
                active = await cur.fetchone()
            async with db.execute("SELECT COUNT(*) FROM users WHERE status = 'banned'") as cur:
                banned = await cur.fetchone()
        
        await update.message.reply_text(
            f"📊 **System Stats**\n\n"
            f"👥 Total Users: {total[0]}\n"
            f"✅ Active: {active[0]}\n"
            f"🚫 Banned: {banned[0]}\n"
            f"🔐 Accounts: {accounts[0]}",
            parse_mode='Markdown',
            reply_markup=get_admin_keyboard()
        )
        return
    
    # ===== ইউজার স্ট্যাটস =====
    if message == "📊 User Stats":
        await update.message.reply_text(
            "👤 Enter Telegram ID to view stats:",
            reply_markup=get_back_keyboard()
        )
        context.user_data['admin_state'] = 'user_stats'
        return
    
    # ===== অ্যাড ক্রেডিট =====
    if message == "➕ Add Credit":
        await update.message.reply_text(
            "👤 Enter Telegram ID:",
            reply_markup=get_back_keyboard()
        )
        context.user_data['admin_state'] = 'add_id'
        return
    
    # ===== রিমুভ ক্রেডিট =====
    if message == "➖ Remove Credit":
        await update.message.reply_text(
            "👤 Enter Telegram ID:",
            reply_markup=get_back_keyboard()
        )
        context.user_data['admin_state'] = 'remove_id'
        return
    
    # ===== ইউজার ব্যান =====
    if message == "🚫 User Ban":
        await update.message.reply_text(
            "👤 Enter Telegram ID to BAN:",
            reply_markup=get_back_keyboard()
        )
        context.user_data['admin_state'] = 'ban_id'
        return
    
    # ===== ইউজার আনব্যান =====
    if message == "✅ User Unban":
        await update.message.reply_text(
            "👤 Enter Telegram ID to UNBAN:",
            reply_markup=get_back_keyboard()
        )
        context.user_data['admin_state'] = 'unban_id'
        return
    
    # ===== ব্রডকাস্ট =====
    if message == "📣 Broadcast":
        await update.message.reply_text(
            "📢 Send your broadcast message:",
            reply_markup=get_back_keyboard()
        )
        context.user_data['admin_state'] = 'broadcast'
        return
    
    # ===== ক্রিয়েট রিডিম কোড =====
    if message == "🎟 Create Redeem Code":
        await update.message.reply_text(
            "🎟 Enter code name (e.g., FREE50):",
            reply_markup=get_back_keyboard()
        )
        context.user_data['admin_state'] = 'code_name'
        return
    
    # ===== ক্রিয়েট অ্যাকাউন্ট =====
    if message == "🔐 Create Account":
        await update.message.reply_text(
            "👤 Enter username:",
            reply_markup=get_back_keyboard()
        )
        context.user_data['admin_state'] = 'acc_user'
        return
    
    # ===== অ্যাডমিন স্টেট প্রসেস =====
    if context.user_data.get('admin_state'):
        await process_admin_states(update, context)

# ===================== অ্যাডমিন স্টেট প্রসেস =====================
async def process_admin_states(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """অ্যাডমিন স্টেট প্রসেস"""
    user_id = update.effective_user.id
    message = update.message.text
    state = context.user_data.get('admin_state')
    
    # ===== ইউজার স্ট্যাটস =====
    if state == 'user_stats':
        try:
            target_id = int(message)
            async with aiosqlite.connect("bot_database.db") as db:
                async with db.execute(
                    "SELECT username, balance, status, join_date FROM users WHERE user_id = ?",
                    (target_id,)
                ) as cur:
                    row = await cur.fetchone()
                    
                    if row:
                        await update.message.reply_text(
                            f"📊 **User Stats**\n\n"
                            f"🆔 ID: `{target_id}`\n"
                            f"👤 Username: {row[0] or 'N/A'}\n"
                            f"💰 Balance: {row[1]}\n"
                            f"🚦 Status: {row[2].capitalize()}\n"
                            f"📅 Joined: {row[3]}",
                            parse_mode='Markdown',
                            reply_markup=get_admin_keyboard()
                        )
                    else:
                        await update.message.reply_text(
                            f"❌ User {target_id} not found!",
                            reply_markup=get_admin_keyboard()
                        )
            context.user_data['admin_state'] = None
        except ValueError:
            await update.message.reply_text("❌ Invalid ID! Enter a number.")
            context.user_data['admin_state'] = None
    
    # ===== অ্যাড ক্রেডিট =====
    elif state == 'add_id':
        try:
            target_id = int(message)
            context.user_data['target_id'] = target_id
            context.user_data['admin_state'] = 'add_amount'
            await update.message.reply_text("💰 Enter amount to add:")
        except ValueError:
            await update.message.reply_text("❌ Invalid ID! Enter a number.")
            context.user_data['admin_state'] = None
    
    elif state == 'add_amount':
        try:
            amount = int(message)
            target_id = context.user_data.get('target_id')
            
            async with aiosqlite.connect("bot_database.db") as db:
                await db.execute(
                    "UPDATE users SET balance = balance + ? WHERE user_id = ?",
                    (amount, target_id)
                )
                await db.commit()
            
            await update.message.reply_text(
                f"✅ Added {amount} credits to user {target_id}.",
                reply_markup=get_admin_keyboard()
            )
            context.user_data['admin_state'] = None
        except ValueError:
            await update.message.reply_text("❌ Invalid amount!")
            context.user_data['admin_state'] = None
    
    # ===== রিমুভ ক্রেডিট =====
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
            
            async with aiosqlite.connect("bot_database.db") as db:
                async with db.execute("SELECT balance FROM users WHERE user_id = ?", (target_id,)) as cur:
                    row = await cur.fetchone()
                    if not row:
                        await update.message.reply_text(f"❌ User {target_id} not found!")
                        context.user_data['admin_state'] = None
                        return
                    
                    if row[0] < amount:
                        await update.message.reply_text(
                            f"❌ User has only {row[0]} credits. Cannot remove {amount}.",
                            reply_markup=get_admin_keyboard()
                        )
                        context.user_data['admin_state'] = None
                        return
                
                await db.execute(
                    "UPDATE users SET balance = balance - ? WHERE user_id = ?",
                    (amount, target_id)
                )
                await db.commit()
            
            await update.message.reply_text(
                f"✅ Removed {amount} credits from user {target_id}.",
                reply_markup=get_admin_keyboard()
            )
            context.user_data['admin_state'] = None
        except ValueError:
            await update.message.reply_text("❌ Invalid amount!")
            context.user_data['admin_state'] = None
    
    # ===== ব্যান =====
    elif state == 'ban_id':
        try:
            target_id = int(message)
            if target_id == ADMIN_ID:
                await update.message.reply_text("❌ Cannot ban Admin!")
                context.user_data['admin_state'] = None
                return
            
            async with aiosqlite.connect("bot_database.db") as db:
                await db.execute(
                    "UPDATE users SET status = 'banned' WHERE user_id = ?",
                    (target_id,)
                )
                await db.commit()
            
            await update.message.reply_text(
                f"🚫 User {target_id} banned!",
                reply_markup=get_admin_keyboard()
            )
            context.user_data['admin_state'] = None
        except ValueError:
            await update.message.reply_text("❌ Invalid ID!")
            context.user_data['admin_state'] = None
    
    # ===== আনব্যান =====
    elif state == 'unban_id':
        try:
            target_id = int(message)
            
            async with aiosqlite.connect("bot_database.db") as db:
                await db.execute(
                    "UPDATE users SET status = 'active' WHERE user_id = ?",
                    (target_id,)
                )
                await db.commit()
            
            await update.message.reply_text(
                f"✅ User {target_id} unbanned!",
                reply_markup=get_admin_keyboard()
            )
            context.user_data['admin_state'] = None
        except ValueError:
            await update.message.reply_text("❌ Invalid ID!")
            context.user_data['admin_state'] = None
    
    # ===== ব্রডকাস্ট =====
    elif state == 'broadcast':
        broadcast_text = message
        
        async with aiosqlite.connect("bot_database.db") as db:
            async with db.execute("SELECT user_id FROM users WHERE status = 'active'") as cur:
                users = await cur.fetchall()
        
        await update.message.reply_text(f"⏳ Broadcasting to {len(users)} users...")
        
        success = 0
        failed = 0
        
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
                failed += 1
        
        await update.message.reply_text(
            f"✅ Broadcast Complete!\n"
            f"📤 Sent: {success}\n"
            f"❌ Failed: {failed}",
            reply_markup=get_admin_keyboard()
        )
        context.user_data['admin_state'] = None
    
    # ===== রিডিম কোড =====
    elif state == 'code_name':
        code = message.strip().upper()
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
            
            async with aiosqlite.connect("bot_database.db") as db:
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
                parse_mode='Markdown',
                reply_markup=get_admin_keyboard()
            )
            context.user_data['admin_state'] = None
        except ValueError:
            await update.message.reply_text("❌ Invalid number!")
            context.user_data['admin_state'] = None
        except aiosqlite.IntegrityError:
            await update.message.reply_text(
                f"❌ Code '{code}' already exists!",
                reply_markup=get_admin_keyboard()
            )
            context.user_data['admin_state'] = None
    
    # ===== অ্যাকাউন্ট ক্রিয়েট =====
    elif state == 'acc_user':
        username = message.strip()
        context.user_data['acc_user'] = username
        context.user_data['admin_state'] = 'acc_pass'
        await update.message.reply_text("🔑 Enter password:")
    
    elif state == 'acc_pass':
        password = message.strip()
        username = context.user_data.get('acc_user')
        
        async with aiosqlite.connect("bot_database.db") as db:
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
                    parse_mode='Markdown',
                    reply_markup=get_admin_keyboard()
                )
            except aiosqlite.IntegrityError:
                await update.message.reply_text(
                    f"❌ Username '{username}' already exists!",
                    reply_markup=get_admin_keyboard()
                )
        
        context.user_data['admin_state'] = None

# ===================== SMS প্রসেস =====================
async def process_sms_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """SMS নম্বর প্রসেস"""
    number = update.message.text.strip()
    
    if not number.isdigit() or len(number) < 11:
        await update.message.reply_text("❌ Invalid number! Enter 11 digits:")
        return
    
    context.user_data['sms_number'] = number
    context.user_data['state'] = 'sms_message'
    
    await update.message.reply_text(
        f"✅ Number: {number}\n\n💬 Enter your message:",
        reply_markup=get_back_keyboard()
    )

async def process_sms_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """SMS মেসেজ প্রসেস"""
    user_id = update.effective_user.id
    number = context.user_data.get('sms_number')
    sms_text = update.message.text
    
    # ব্যালেন্স চেক
    async with aiosqlite.connect("bot_database.db") as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if not row or row[0] < 1:
                await update.message.reply_text(f"❌ Insufficient credits! Contact: {ADMIN_USERNAME}")
                context.user_data.clear()
                return
    
    await update.message.reply_text(f"⏳ Sending SMS to {number}...")
    
    # SMS পাঠানো
    success = False
    response_text = ""
    
    try:
        params = {"key": SMS_API_KEY, "number": number, "msg": sms_text}
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
        response_text = f"Error: {str(e)}"
    
    if success:
        async with aiosqlite.connect("bot_database.db") as db:
            await db.execute("UPDATE users SET balance = balance - 1 WHERE user_id = ?", (user_id,))
            await db.commit()
        
        await update.message.reply_text(
            f"✅ SMS Sent Successfully!\n💰 1 Credit deducted.",
            reply_markup=get_main_keyboard()
        )
    else:
        await update.message.reply_text(
            f"❌ Failed to send SMS!\n⚠️ {response_text[:100]}",
            reply_markup=get_main_keyboard()
        )
    
    context.user_data.clear()

# ===================== BOMBER প্রসেস =====================
async def process_bomber_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bomber নম্বর প্রসেস"""
    number = update.message.text.strip()
    
    if not number.isdigit() or len(number) < 11:
        await update.message.reply_text("❌ Invalid number! Enter 11 digits:")
        return
    
    context.user_data['bomber_number'] = number
    context.user_data['state'] = 'bomber_amount'
    
    await update.message.reply_text(
        f"✅ Number: {number}\n\n💥 Enter amount (1-100):",
        reply_markup=get_back_keyboard()
    )

async def process_bomber_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bomber অ্যামাউন্ট প্রসেস"""
    user_id = update.effective_user.id
    number = context.user_data.get('bomber_number')
    
    try:
        amount = int(update.message.text.strip())
        if amount < 1 or amount > 100:
            await update.message.reply_text("❌ Amount must be 1-100!")
            return
    except ValueError:
        await update.message.reply_text("❌ Enter a valid number!")
        return
    
    msg = await update.message.reply_text(
        f"⏳ Bombing {number} ({amount} times)...\nPlease wait..."
    )
    
    success_count = 0
    
    for i in range(amount):
        try:
            response = requests.get(f"{BOMBER_API_URL}{number}", timeout=10)
            data = response.json()
            if data.get('success', 0) > 0:
                success_count += data.get('success', 0)
        except:
            pass
        
        if (i + 1) % 5 == 0 or (i + 1) == amount:
            try:
                await msg.edit_text(
                    f"⏳ Bombing...\n"
                    f"✅ Success: {success_count}\n"
                    f"📊 Progress: {i+1}/{amount}"
                )
            except:
                pass
        
        await asyncio.sleep(0.3)
    
    await msg.edit_text(
        f"✅ Bombing Complete!\n\n"
        f"📱 Target: {number}\n"
        f"💥 Total: {amount}\n"
        f"✅ Success: {success_count}",
        reply_markup=get_main_keyboard()
    )
    
    context.user_data.clear()

# ===================== প্রোফাইল =====================
async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """প্রোফাইল দেখায়"""
    user_id = update.effective_user.id
    
    async with aiosqlite.connect("bot_database.db") as db:
        async with db.execute(
            "SELECT username, balance, status FROM users WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            
            if row:
                await update.message.reply_text(
                    f"👤 **My Profile**\n\n"
                    f"🆔 ID: `{user_id}`\n"
                    f"👤 Username: {row[0] or 'N/A'}\n"
                    f"💰 Credits: {row[1]}\n"
                    f"🚦 Status: {row[2].capitalize()}\n\n"
                    f"👨‍💻 Admin: {ADMIN_USERNAME}",
                    parse_mode="Markdown",
                    reply_markup=get_main_keyboard()
                )
            else:
                await update.message.reply_text(
                    "❌ User not found! Please /start again.",
                    reply_markup=get_main_keyboard()
                )

# ===================== স্ট্যাটস =====================
async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """স্ট্যাটস দেখায়"""
    user_id = update.effective_user.id
    
    async with aiosqlite.connect("bot_database.db") as db:
        async with db.execute(
            "SELECT balance FROM users WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            balance = row[0] if row else 0
    
    await update.message.reply_text(
        f"📊 **My Stats**\n\n"
        f"💰 Current Balance: {balance}\n"
        f"📨 SMS Sent: 0\n"
        f"💣 Bombing Done: 0\n\n"
        f"📌 Use Send SMS or SMS Bomber!",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

# ===================== রিডিম =====================
async def process_redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """রিডিম প্রসেস"""
    user_id = update.effective_user.id
    code = update.message.text.strip().upper()
    
    async with aiosqlite.connect("bot_database.db") as db:
        # চেক করা ইউজার আগে ব্যবহার করেছে কিনা
        async with db.execute("SELECT 1 FROM redeem_history WHERE user_id = ? AND code = ?", (user_id, code)) as cur:
            if await cur.fetchone():
                await update.message.reply_text("❌ You already used this code!")
                context.user_data.clear()
                return
        
        async with db.execute("SELECT amount, usages FROM redeem_codes WHERE code = ?", (code,)) as cursor:
            row = await cursor.fetchone()
            
            if not row or row[1] <= 0:
                await update.message.reply_text("❌ Invalid or expired code!")
                context.user_data.clear()
                return
            
            amount = row[0]
            await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
            await db.execute("UPDATE redeem_codes SET usages = usages - 1 WHERE code = ?", (code,))
            await db.execute("INSERT OR IGNORE INTO redeem_history (user_id, code) VALUES (?, ?)", (user_id, code))
            await db.commit()
    
    await update.message.reply_text(
        f"🎉 Code Redeemed!\n✅ +{amount} Credits!",
        reply_markup=get_main_keyboard()
    )
    context.user_data.clear()

# ===================== মেইন =====================
async def main():
    """বট চালু"""
    try:
        print("="*50)
        print("🤖 Starting Unified SMS Bot...")
        print(f"Token: {BOT_TOKEN[:15]}...")
        print(f"👑 Admin ID: {ADMIN_ID}")
        
        # ডাটাবেস ইনিশিয়ালাইজ
        await init_db()
        
        # অ্যাপ্লিকেশন
        application = Application.builder().token(BOT_TOKEN).build()
        
        # হ্যান্ডলার
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        print("✅ Bot is ready! Starting polling...")
        print("="*50)
        
        # পোলিং স্টার্ট
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        
        # বট চালু রাখা
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
