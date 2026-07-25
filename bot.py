import asyncio
import logging
import aiosqlite
import aiohttp
import requests
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ===================== কনফিগারেশন =====================
BOT_TOKEN = "8826486988:AAFOOfdcrVCgvj532plzOQUXwx40yn3USl0"
ADMIN_ID = 1967494059
ADMIN_USERNAME = "@RobiEntertainment"
OWNER_USERNAME = "@RobiEntertainment"

# API
SMS_API_URL = "https://api.paglahost.shop/Custom_SMS/api.php"
SMS_API_KEY = "Shuvo55356"
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
                balance INTEGER DEFAULT 10,
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
            
            await db.execute(
                "INSERT OR IGNORE INTO redeem_codes (code, amount, usages) VALUES ('FREE50', 50, 100)"
            )
            
            await db.commit()
            logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"Database error: {e}")

# ===================== কীবোর্ড =====================
def get_main_keyboard():
    keyboard = [
        ["📨 Send SMS", "💣 SMS Bomber"],
        ["👤 My Profile", "🎁 Redeem Code"],
        ["📊 My Stats", "📞 Contact Admin"],
        ["🤖 AI Tools"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_back_keyboard():
    keyboard = [["🔙 Back"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_ai_keyboard():
    keyboard = [
        ["🤖 ChatGPT", "🎨 PicWish"],
        ["🔍 Perplexity", "🎵 Suno AI"],
        ["🎨 Canva", "🎤 ElevenLabs"],
        ["✍️ Grammarly", "🎬 Luma AI"],
        ["📊 RecCloud", "🎥 Runway ML"],
        ["🎧 Descript", "🖼 SkySnail"],
        ["🔙 Back"]
    ]
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
        f"💰 Balance: 10 Credits\n\n"
        f"📌 **Select an option:**",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

# ===================== SMS =====================
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
        "📱 **Enter phone number:**\n"
        "Example: `018XXXXXXXX`",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard()
    )
    context.user_data['state'] = 'sms_number'

async def sms_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    number = update.message.text.strip()
    
    if not number.isdigit() or len(number) != 11:
        await update.message.reply_text(
            "❌ **Invalid number!**\n"
            "Enter 11 digits: `018XXXXXXXX`",
            parse_mode="Markdown",
            reply_markup=get_back_keyboard()
        )
        return
    
    context.user_data['number'] = number
    context.user_data['state'] = 'sms_message'
    
    await update.message.reply_text(
        f"✅ Number: `{number}`\n\n"
        f"💬 **Enter your message:**",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard()
    )

async def sms_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    number = context.user_data.get('number')
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
            await db.commit()
        
        await update.message.reply_text(
            f"✅ **SMS Sent Successfully!**\n\n"
            f"📱 Number: `{number}`\n"
            f"💰 1 Credit deducted",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
    else:
        await update.message.reply_text(
            f"❌ **Failed to send SMS!**\n\n"
            f"📱 Number: `{number}`\n"
            f"⚠️ Error: `{response_text[:50]}`",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
    
    context.user_data.clear()

# ===================== BOMBER =====================
async def cmd_bomber(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💣 **SMS Bomber**\n\n"
        "Enter target number:\n"
        "Example: `018XXXXXXXX`\n"
        "⚠️ Max 100 messages",
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
        f"💥 **Enter amount (1-100):**",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard()
    )

async def bomber_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    number = context.user_data.get('bomber_number')
    
    try:
        amount = int(update.message.text.strip())
        if amount < 1 or amount > 100:
            await update.message.reply_text("❌ Amount must be 1-100!", reply_markup=get_back_keyboard())
            return
    except ValueError:
        await update.message.reply_text("❌ Enter a valid number!", reply_markup=get_back_keyboard())
        return
    
    if not number:
        await update.message.reply_text("❌ Error! Start again.", reply_markup=get_main_keyboard())
        context.user_data.clear()
        return
    
    msg = await update.message.reply_text(
        f"⏳ Bombing `{number}` ({amount} times)...",
        parse_mode="Markdown"
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
        
        if (i + 1) % 10 == 0 or (i + 1) == amount:
            try:
                await msg.edit_text(
                    f"⏳ Bombing...\n"
                    f"✅ Success: {success_count}\n"
                    f"📊 Progress: {i+1}/{amount}"
                )
            except:
                pass
        
        await asyncio.sleep(0.2)
    
    await msg.edit_text(
        f"✅ **Bombing Complete!**\n\n"
        f"📱 Target: `{number}`\n"
        f"💥 Total: {amount}\n"
        f"✅ Success: {success_count}\n"
        f"📊 Rate: {round((success_count/amount)*100, 2)}%",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )
    
    context.user_data.clear()

# ===================== প্রোফাইল =====================
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    async with aiosqlite.connect("bot_database.db") as db:
        async with db.execute(
            "SELECT username, balance, status, join_date FROM users WHERE user_id = ?",
            (user_id,)
        ) as cur:
            row = await cur.fetchone()
    
    if row:
        await update.message.reply_text(
            f"👤 **My Profile**\n\n"
            f"🆔 ID: `{user_id}`\n"
            f"👤 Username: {row[0] or 'N/A'}\n"
            f"💰 Balance: {row[1]}\n"
            f"🚦 Status: {row[2].capitalize()}\n"
            f"📅 Joined: {row[3][:10] if row[3] else 'N/A'}",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )

# ===================== স্ট্যাটস =====================
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    async with aiosqlite.connect("bot_database.db") as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
            balance = row[0] if row else 0
    
    await update.message.reply_text(
        f"📊 **My Stats**\n\n"
        f"💰 Balance: {balance}\n"
        f"📨 SMS Sent: 0\n"
        f"💣 Bombing Done: 0\n\n"
        f"📌 Use 'Send SMS' or 'SMS Bomber'!",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

# ===================== রিডিম =====================
async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎟 **Enter Redeem Code:**",
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
        f"🎉 **Code Redeemed!**\n\n"
        f"✅ +{amount} Credits added!",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )
    context.user_data.clear()

# ===================== AI টুলস =====================
async def ai_tools(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **AI Tools Hub**\n\n"
        "Select a tool:",
        parse_mode="Markdown",
        reply_markup=get_ai_keyboard()
    )

async def ai_tool_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tool_map = {
        "🤖 ChatGPT": "https://chatgpt.com",
        "🎨 PicWish": "https://picwish.com",
        "🔍 Perplexity": "https://perplexity.ai",
        "🎵 Suno AI": "https://suno.ai",
        "🎨 Canva": "https://canva.com",
        "🎤 ElevenLabs": "https://elevenlabs.io",
        "✍️ Grammarly": "https://grammarly.com",
        "🎬 Luma AI": "https://luma.ai",
        "📊 RecCloud": "https://reccloud.com",
        "🎥 Runway ML": "https://runway.ml",
        "🎧 Descript": "https://descript.com",
        "🖼 SkySnail": "https://skysnail.io"
    }
    
    tool_name = update.message.text
    url = tool_map.get(tool_name)
    
    if url:
        await update.message.reply_text(
            f"🔗 **{tool_name}**\n\n"
            f"Visit: {url}\n\n"
            f"💡 Click the link to use!",
            parse_mode="Markdown",
            reply_markup=get_ai_keyboard()
        )
    else:
        await update.message.reply_text("❌ Tool not found!", reply_markup=get_ai_keyboard())

# ===================== কন্টাক্ট =====================
async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📞 **Contact**\n\n"
        f"👨‍💻 Admin: {ADMIN_USERNAME}\n"
        f"👨‍💻 Owner: {OWNER_USERNAME}",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

# ===================== মেসেজ হ্যান্ডলার =====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message.text
    
    logger.info(f"📩 Message from {user_id}: {message}")
    
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
    
    if message == "🤖 AI Tools":
        await ai_tools(update, context)
        return
    
    # ===== AI টুলস =====
    if message in ["🤖 ChatGPT", "🎨 PicWish", "🔍 Perplexity", "🎵 Suno AI",
                   "🎨 Canva", "🎤 ElevenLabs", "✍️ Grammarly", "🎬 Luma AI",
                   "📊 RecCloud", "🎥 Runway ML", "🎧 Descript", "🖼 SkySnail"]:
        await ai_tool_handler(update, context)
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
    
    # ===== ডিফল্ট =====
    await update.message.reply_text(
        "❌ **Please use the buttons below:**",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

# ===================== মেইন =====================
async def main():
    try:
        print("="*60)
        print("🔥 BOT STARTING...")
        print(f"✅ Token: {BOT_TOKEN[:15]}...")
        print(f"👑 Admin: {ADMIN_ID}")
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
