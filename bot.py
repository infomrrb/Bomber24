import asyncio
import logging
import aiosqlite
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ===================== কনফিগারেশন =====================
BOT_TOKEN = "8826486988:AAFOOfdcrVCgvj532plzOQUXwx40yn3USl0"
ADMIN_ID = 1967494059
ADMIN_USERNAME = "@RobiEntertainment"
OWNER_USERNAME = "@RobiEntertainment"

# AI টুলস ডাটা
AI_TOOLS = {
    "chatgpt": {
        "name": "ChatGPT",
        "url": "https://chatgpt.com",
        "desc": "যেকোনো প্রবলেম সলভ করতে",
        "emoji": "🤖",
        "power": "🔥🔥🔥🔥🔥"
    },
    "picwish": {
        "name": "PicWish",
        "url": "https://picwish.com",
        "desc": "এক ক্লিকে ব্যাকগ্রাউন্ড রিমুভ করতে",
        "emoji": "🎨",
        "power": "🔥🔥🔥🔥"
    },
    "perplexity": {
        "name": "Perplexity AI",
        "url": "https://perplexity.ai",
        "desc": "যেকোনো টপিক ডিপ রিসার্চ করতে",
        "emoji": "🔍",
        "power": "🔥🔥🔥🔥🔥"
    },
    "suno": {
        "name": "Suno AI",
        "url": "https://suno.ai",
        "desc": "নিজে নিজে মিউজিক কম্পোজ করতে",
        "emoji": "🎵",
        "power": "🔥🔥🔥🔥"
    },
    "canva": {
        "name": "Canva",
        "url": "https://canva.com",
        "desc": "প্রফেশনাল গ্রাফিক্স ডিজাইন করতে",
        "emoji": "🎨",
        "power": "🔥🔥🔥🔥🔥"
    },
    "elevenlabs": {
        "name": "ElevenLabs",
        "url": "https://elevenlabs.io",
        "desc": "যেকোনো ভয়েস ক্লোন করতে",
        "emoji": "🎤",
        "power": "🔥🔥🔥🔥🔥"
    },
    "grammarly": {
        "name": "Grammarly",
        "url": "https://grammarly.com",
        "desc": "ইংলিশ রাইটিং পারফেক্ট করতে",
        "emoji": "✍️",
        "power": "🔥🔥🔥🔥"
    },
    "luma": {
        "name": "Luma AI",
        "url": "https://luma.ai",
        "desc": "টেক্সট থেকে ভিডিও বানাতে",
        "emoji": "🎬",
        "power": "🔥🔥🔥🔥"
    },
    "reccloud": {
        "name": "RecCloud",
        "url": "https://reccloud.com",
        "desc": "বড় ইউটিউব ভিডিও সামারাইজ করতে",
        "emoji": "📊",
        "power": "🔥🔥🔥"
    },
    "runway": {
        "name": "Runway ML",
        "url": "https://runway.ml",
        "desc": "প্রো-লেভেলের ভিডিও এডিট করতে",
        "emoji": "🎥",
        "power": "🔥🔥🔥🔥🔥"
    },
    "descript": {
        "name": "Descript",
        "url": "https://descript.com",
        "desc": "পডকাস্ট বা অডিও এডিট করতে",
        "emoji": "🎧",
        "power": "🔥🔥🔥🔥"
    },
    "skysnail": {
        "name": "SkySnail",
        "url": "https://skysnail.io",
        "desc": "ভাইরাল থাম্বনেইল বানাতে",
        "emoji": "🖼",
        "power": "🔥🔥🔥🔥"
    }
}

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
            await db.execute("""CREATE TABLE IF NOT EXISTS ai_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                tool_name TEXT,
                usage_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            
            await db.execute("""CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance INTEGER DEFAULT 0,
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active'
            )""")
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

def get_ai_tools_keyboard():
    keyboard = [
        ["🤖 ChatGPT", "🎨 PicWish"],
        ["🔍 Perplexity AI", "🎵 Suno AI"],
        ["🎨 Canva", "🎤 ElevenLabs"],
        ["✍️ Grammarly", "🎬 Luma AI"],
        ["📊 RecCloud", "🎥 Runway ML"],
        ["🎧 Descript", "🖼 SkySnail"],
        ["🔙 Back"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_back_keyboard():
    keyboard = [["🔙 Back"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_admin_keyboard():
    keyboard = [
        ["➕ Add Credit", "➖ Remove Credit"],
        ["🚫 User Ban", "✅ User Unban"],
        ["📣 Broadcast", "🎟 Create Redeem Code"],
        ["👥 Total Users", "📊 AI Stats"],
        ["⬅️ Back to User"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ===================== স্টার্ট =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    if user_id == ADMIN_ID:
        await update.message.reply_text(
            f"👑 **Admin Panel**\n\nWelcome Admin!",
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

# ===================== AI টুলস =====================
async def show_ai_tools(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **AI Tools Hub**\n\n"
        "Powerful AI tools at your fingertips:\n\n"
        "• 🤖 ChatGPT - Problem Solving\n"
        "• 🎨 PicWish - Remove Background\n"
        "• 🔍 Perplexity AI - Deep Research\n"
        "• 🎵 Suno AI - Music Generation\n"
        "• 🎨 Canva - Graphic Design\n"
        "• 🎤 ElevenLabs - Voice Cloning\n"
        "• ✍️ Grammarly - Perfect Writing\n"
        "• 🎬 Luma AI - Text to Video\n"
        "• 📊 RecCloud - Video Summarizer\n"
        "• 🎥 Runway ML - Video Editing\n"
        "• 🎧 Descript - Audio Editing\n"
        "• 🖼 SkySnail - Thumbnail Creator\n\n"
        "Select a tool below:",
        parse_mode="Markdown",
        reply_markup=get_ai_tools_keyboard()
    )

async def handle_ai_tool(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    tool_name = update.message.text
    
    tool_map = {
        "🤖 ChatGPT": "chatgpt",
        "🎨 PicWish": "picwish",
        "🔍 Perplexity AI": "perplexity",
        "🎵 Suno AI": "suno",
        "🎨 Canva": "canva",
        "🎤 ElevenLabs": "elevenlabs",
        "✍️ Grammarly": "grammarly",
        "🎬 Luma AI": "luma",
        "📊 RecCloud": "reccloud",
        "🎥 Runway ML": "runway",
        "🎧 Descript": "descript",
        "🖼 SkySnail": "skysnail"
    }
    
    tool_key = tool_map.get(tool_name)
    if not tool_key:
        await update.message.reply_text("❌ Tool not found!")
        return
    
    tool_info = AI_TOOLS.get(tool_key)
    if not tool_info:
        await update.message.reply_text("❌ Tool info not found!")
        return
    
    # ইউজ হিস্টরি সেভ
    try:
        async with aiosqlite.connect("bot_database.db") as db:
            await db.execute(
                "INSERT INTO ai_usage (user_id, tool_name) VALUES (?, ?)",
                (user_id, tool_key)
            )
            await db.commit()
    except Exception as e:
        logger.error(f"Usage save error: {e}")
    
    await update.message.reply_text(
        f"{tool_info['emoji']} **{tool_info['name']}**\n\n"
        f"📌 {tool_info['desc']}\n\n"
        f"🔗 **Visit:** {tool_info['url']}\n\n"
        f"💡 **How to use:**\n"
        f"1. Click the link above\n"
        f"2. Follow the instructions\n"
        f"3. Get amazing results!\n\n"
        f"⭐ **Power:** {tool_info['power']}\n\n"
        f"🆓 Free tier available!",
        parse_mode="Markdown",
        reply_markup=get_ai_tools_keyboard()
    )

# ===================== অ্যাডমিন এআই স্ট্যাটস =====================
async def admin_ai_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    try:
        async with aiosqlite.connect("bot_database.db") as db:
            # মোট ব্যবহার
            async with db.execute("SELECT COUNT(*) FROM ai_usage") as cur:
                total = await cur.fetchone()
            
            # টুল ভিত্তিক ব্যবহার
            tool_stats = {}
            for key in AI_TOOLS:
                async with db.execute(
                    "SELECT COUNT(*) FROM ai_usage WHERE tool_name = ?",
                    (key,)
                ) as cur:
                    count = await cur.fetchone()
                    tool_stats[key] = count[0] if count else 0
            
            # মোট ইউজার
            async with db.execute("SELECT COUNT(DISTINCT user_id) FROM ai_usage") as cur:
                users = await cur.fetchone()
        
        response = "📊 **AI Tools Statistics**\n\n"
        response += f"📈 Total Usage: {total[0] if total else 0}\n"
        response += f"👥 Total Users: {users[0] if users else 0}\n\n"
        response += "**🏆 Tool Rankings:**\n"
        
        sorted_tools = sorted(tool_stats.items(), key=lambda x: x[1], reverse=True)
        for i, (key, count) in enumerate(sorted_tools, 1):
            name = AI_TOOLS.get(key, {}).get('name', key)
            emoji = AI_TOOLS.get(key, {}).get('emoji', '')
            response += f"{i}. {emoji} {name}: {count} uses\n"
        
        await update.message.reply_text(response, parse_mode="Markdown")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error fetching stats: {str(e)}")

# ===================== মেসেজ হ্যান্ডলার =====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message.text
    
    # অ্যাডমিন কমান্ড
    if user_id == ADMIN_ID:
        if message == "📊 AI Stats":
            await admin_ai_stats(update, context)
            return
        if message == "⬅️ Back to User":
            await update.message.reply_text("Switched to User Mode", reply_markup=get_main_keyboard())
            return
    
    # AI Tools
    if message == "🤖 AI Tools":
        await show_ai_tools(update, context)
        return
    
    # AI Tool Selection
    if message in ["🤖 ChatGPT", "🎨 PicWish", "🔍 Perplexity AI", "🎵 Suno AI", 
                   "🎨 Canva", "🎤 ElevenLabs", "✍️ Grammarly", "🎬 Luma AI",
                   "📊 RecCloud", "🎥 Runway ML", "🎧 Descript", "🖼 SkySnail"]:
        await handle_ai_tool(update, context)
        return
    
    # Back
    if message == "🔙 Back":
        await update.message.reply_text("🏠 Main Menu", reply_markup=get_main_keyboard())
        context.user_data.clear()
        return
    
    # অন্যান্য কমান্ড
    if message == "📨 Send SMS":
        await update.message.reply_text("📱 Enter phone number:", reply_markup=get_back_keyboard())
        context.user_data['state'] = 'sms_number'
        return
    
    if message == "💣 SMS Bomber":
        await update.message.reply_text("💣 Enter target number:", reply_markup=get_back_keyboard())
        context.user_data['state'] = 'bomber_number'
        return
    
    if message == "👤 My Profile":
        async with aiosqlite.connect("bot_database.db") as db:
            async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cur:
                row = await cur.fetchone()
                balance = row[0] if row else 0
        
        await update.message.reply_text(
            f"👤 **My Profile**\n\n"
            f"🆔 ID: `{user_id}`\n"
            f"💰 Balance: {balance}\n"
            f"👨‍💻 Admin: {ADMIN_USERNAME}",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        return
    
    if message == "🎁 Redeem Code":
        await update.message.reply_text("🎟 Enter redeem code:", reply_markup=get_back_keyboard())
        context.user_data['state'] = 'redeem_code'
        return
    
    if message == "📊 My Stats":
        await update.message.reply_text(
            "📊 **My Stats**\n\n"
            "📨 SMS Sent: 0\n"
            "💣 Bombing Done: 0\n"
            "🤖 AI Tools Used: 0",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        return
    
    if message == "📞 Contact Admin":
        await update.message.reply_text(
            f"📞 **Contact Admin**\n\n"
            f"👨‍💻 Admin: {ADMIN_USERNAME}\n"
            f"👨‍💻 Owner: {OWNER_USERNAME}",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        return
    
    # স্টেট প্রসেস
    state = context.user_data.get('state')
    if state == 'sms_number':
        await update.message.reply_text(f"✅ SMS sent to {message}!", reply_markup=get_main_keyboard())
        context.user_data.clear()
        return
    
    if state == 'redeem_code':
        await update.message.reply_text(f"🎉 Code {message} redeemed!", reply_markup=get_main_keyboard())
        context.user_data.clear()
        return
    
    await update.message.reply_text(
        "❌ Please use the buttons below:",
        reply_markup=get_main_keyboard()
    )

# ===================== মেইন =====================
async def main():
    try:
        print("="*60)
        print("🤖 AI Tools Bot Starting...")
        print(f"✅ Tools Available: {len(AI_TOOLS)}")
        print(f"👑 Admin ID: {ADMIN_ID}")
        print("="*60)
        
        await init_db()
        
        application = Application.builder().token(BOT_TOKEN).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        
        print("✅ Bot is running!")
        
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
