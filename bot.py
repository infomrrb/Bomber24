import asyncio
import logging
import requests
import aiosqlite
import aiohttp
import json
import re
import os
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

# DOWNLOADER API
DOWNLOAD_API_URL = "https://api.helll.workers.dev/api?url="

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
            # ইউজার টেবিল
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
            
            # ডাউনলোড হিস্টরি টেবিল
            await db.execute("""CREATE TABLE IF NOT EXISTS download_history (
                user_id INTEGER,
                url TEXT,
                type TEXT,
                download_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    """মেইন মেনু কীবোর্ড (ডাউনলোডার যোগ করা)"""
    keyboard = [
        ["📨 Send SMS", "💣 SMS Bomber"],
        ["👤 My Profile", "🎁 Redeem Code"],
        ["📊 My Stats", "📞 Contact Admin"],
        ["📥 Media Downloader"]  # নতুন ডাউনলোডার বাটন
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_downloader_keyboard():
    """ডাউনলোডার মেনু কীবোর্ড"""
    keyboard = [
        ["📥 YouTube Downloader", "🎵 TikTok Downloader"],
        ["📸 Instagram Downloader", "📹 Facebook Downloader"],
        ["🐦 Twitter/X Downloader"],
        ["📊 Download History", "🔙 Back"]
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

def get_download_options():
    """ভিডিও/অডিও অপশন"""
    keyboard = [
        [
            InlineKeyboardButton("🎬 Video (MP4)", callback_data="download_video"),
            InlineKeyboardButton("🎵 Audio (MP3)", callback_data="download_audio")
        ],
        [
            InlineKeyboardButton("🖼 Thumbnail", callback_data="download_thumbnail"),
            InlineKeyboardButton("❌ Cancel", callback_data="download_cancel")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

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
    
    # ===== ডাউনলোডার =====
    if message == "📥 Media Downloader":
        await show_downloader_menu(update, context)
        return
    
    # ===== ডাউনলোডার সাব-মেনু =====
    if message == "📥 YouTube Downloader":
        await youtube_downloader(update, context)
        return
    
    if message == "🎵 TikTok Downloader":
        await tiktok_downloader(update, context)
        return
    
    if message == "📸 Instagram Downloader":
        await instagram_downloader(update, context)
        return
    
    if message == "📹 Facebook Downloader":
        await facebook_downloader(update, context)
        return
    
    if message == "🐦 Twitter/X Downloader":
        await twitter_downloader(update, context)
        return
    
    if message == "📊 Download History":
        await show_download_history(update, context)
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
    
    # ===== ডাউনলোড URL প্রসেস =====
    if context.user_data.get('downloader_state'):
        await process_download(update, context)
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

# ===================== ডাউনলোডার ফাংশন =====================
async def show_downloader_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ডাউনলোডার মেনু দেখায়"""
    await update.message.reply_text(
        "📥 **Media Downloader**\n\n"
        "Download videos from:\n"
        "• 📥 YouTube\n"
        "• 🎵 TikTok\n"
        "• 📸 Instagram\n"
        "• 📹 Facebook\n"
        "• 🐦 Twitter/X\n\n"
        "🔹 No Watermark\n"
        "🔹 HD Quality\n"
        "🔹 Fast Download\n\n"
        "Select a downloader below:",
        parse_mode="Markdown",
        reply_markup=get_downloader_keyboard()
    )

async def youtube_downloader(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ইউটিউব ডাউনলোডার"""
    await update.message.reply_text(
        "📥 **YouTube Downloader**\n\n"
        "Send any YouTube link:\n"
        "• Video: https://youtube.com/watch?v=xxxx\n"
        "• Shorts: https://youtube.com/shorts/xxxx\n\n"
        "⚠️ Max 10 minutes video allowed.",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard()
    )
    context.user_data['downloader_state'] = 'youtube'

async def tiktok_downloader(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """টিকটক ডাউনলোডার"""
    await update.message.reply_text(
        "🎵 **TikTok Downloader**\n\n"
        "Send any TikTok link:\n"
        "• https://tiktok.com/@username/video/xxxx\n"
        "• https://vm.tiktok.com/xxxx\n\n"
        "✅ No watermark video supported!",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard()
    )
    context.user_data['downloader_state'] = 'tiktok'

async def instagram_downloader(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ইনস্টাগ্রাম ডাউনলোডার"""
    await update.message.reply_text(
        "📸 **Instagram Downloader**\n\n"
        "Send any Instagram link:\n"
        "• Post: https://instagram.com/p/xxxx\n"
        "• Reel: https://instagram.com/reel/xxxx\n\n"
        "⚠️ Private accounts content not supported.",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard()
    )
    context.user_data['downloader_state'] = 'instagram'

async def facebook_downloader(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ফেসবুক ডাউনলোডার"""
    await update.message.reply_text(
        "📹 **Facebook Downloader**\n\n"
        "Send any Facebook link:\n"
        "• Video: https://facebook.com/xxxx\n"
        "• https://fb.watch/xxxx\n\n"
        "⚠️ Public posts only.",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard()
    )
    context.user_data['downloader_state'] = 'facebook'

async def twitter_downloader(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """টুইটার ডাউনলোডার"""
    await update.message.reply_text(
        "🐦 **Twitter/X Downloader**\n\n"
        "Send any Twitter/X link:\n"
        "• https://twitter.com/username/status/xxxx\n"
        "• https://x.com/username/status/xxxx\n\n"
        "✅ Video & GIF supported!",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard()
    )
    context.user_data['downloader_state'] = 'twitter'

# ===================== ডাউনলোড প্রসেসর =====================
async def process_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ডাউনলোড প্রসেস"""
    user_id = update.effective_user.id
    url = update.message.text.strip()
    state = context.user_data.get('downloader_state', '')
    
    # URL ভ্যালিডেশন
    if not url.startswith(('http://', 'https://')):
        await update.message.reply_text("❌ Invalid URL! Please send a valid link.")
        return
    
    # ডাউনলোড টাইপ নির্ধারণ
    download_type = {
        'youtube': 'YouTube',
        'tiktok': 'TikTok',
        'instagram': 'Instagram',
        'facebook': 'Facebook',
        'twitter': 'Twitter'
    }.get(state, 'Unknown')
    
    # প্রসেসিং মেসেজ
    msg = await update.message.reply_text(
        f"⏳ Processing {download_type} download...\n"
        f"🔗 URL: {url[:50]}...\n"
        f"⏰ Please wait..."
    )
    
    try:
        # API কল
        api_url = f"{DOWNLOAD_API_URL}{url}"
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=30) as response:
                if response.status == 200:
                    try:
                        data = await response.json()
                        
                        # API রেসপন্স থেকে ডাটা এক্সট্রাক্ট
                        video_url = data.get('video', data.get('url', ''))
                        audio_url = data.get('audio', data.get('music', ''))
                        thumbnail = data.get('thumbnail', data.get('cover', ''))
                        title = data.get('title', f"{download_type} Video")
                        
                        if video_url or audio_url:
                            # ডাটা সেভ
                            context.user_data['download_data'] = {
                                'video_url': video_url,
                                'audio_url': audio_url,
                                'thumbnail': thumbnail,
                                'title': title,
                                'type': download_type,
                                'url': url
                            }
                            
                            await msg.edit_text(
                                f"✅ Download successful!\n\n"
                                f"📌 Title: {title[:50]}...\n"
                                f"📱 Platform: {download_type}\n\n"
                                f"Select download option:",
                                reply_markup=get_download_options()
                            )
                            return
                        else:
                            await msg.edit_text(
                                f"❌ No downloadable content found!\n"
                                f"💡 Try another link."
                            )
                    except:
                        await msg.edit_text(
                            f"❌ Invalid response from server!\n"
                            f"💡 Try again later."
                        )
                else:
                    await msg.edit_text(
                        f"❌ API Error!\n"
                        f"Status: {response.status}\n\n"
                        f"💡 Try again or use another link."
                    )
                
    except asyncio.TimeoutError:
        await msg.edit_text(
            f"❌ Request timeout!\n"
            f"💡 The server is taking too long. Try again later."
        )
    except Exception as e:
        await msg.edit_text(
            f"❌ Error!\n"
            f"⚠️ {str(e)}"
        )
        logger.error(f"Download error: {e}")

# ===================== ডাউনলোড অপশন হ্যান্ডলার =====================
async def download_options_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ডাউনলোড অপশন হ্যান্ডলার"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    option = query.data
    data = context.user_data.get('download_data', {})
    
    if option == 'download_cancel':
        await query.edit_message_text("❌ Download cancelled.")
        context.user_data['downloader_state'] = None
        return
    
    if not data:
        await query.edit_message_text("❌ No download data found! Please try again.")
        return
    
    video_url = data.get('video_url', '')
    audio_url = data.get('audio_url', '')
    thumbnail = data.get('thumbnail', '')
    title = data.get('title', 'video')
    download_type = data.get('type', '')
    
    if option == 'download_video' and video_url:
        await query.edit_message_text(f"⏳ Downloading video...")
        try:
            await query.message.reply_video(
                video=video_url,
                caption=f"📥 {download_type} Video\n"
                       f"📌 {title[:100]}\n"
                       f"👤 {OWNER_USERNAME}",
                supports_streaming=True,
                write_timeout=60
            )
            await query.message.reply_text("✅ Video sent successfully!")
            
            # হিস্টরি সেভ
            async with aiosqlite.connect("bot_database.db") as db:
                await db.execute(
                    "INSERT INTO download_history (user_id, url, type) VALUES (?, ?, ?)",
                    (user_id, data['url'], 'video')
                )
                await db.commit()
            
        except Exception as e:
            await query.message.reply_text(f"❌ Failed to send video: {str(e)}")
    
    elif option == 'download_audio' and audio_url:
        await query.edit_message_text(f"⏳ Downloading audio...")
        try:
            await query.message.reply_audio(
                audio=audio_url,
                caption=f"🎵 {download_type} Audio\n"
                       f"📌 {title[:100]}\n"
                       f"👤 {OWNER_USERNAME}",
                write_timeout=60
            )
            await query.message.reply_text("✅ Audio sent successfully!")
            
            async with aiosqlite.connect("bot_database.db") as db:
                await db.execute(
                    "INSERT INTO download_history (user_id, url, type) VALUES (?, ?, ?)",
                    (user_id, data['url'], 'audio')
                )
                await db.commit()
            
        except Exception as e:
            await query.message.reply_text(f"❌ Failed to send audio: {str(e)}")
    
    elif option == 'download_thumbnail' and thumbnail:
        await query.edit_message_text(f"⏳ Downloading thumbnail...")
        try:
            await query.message.reply_photo(
                photo=thumbnail,
                caption=f"🖼 {download_type} Thumbnail\n"
                       f"📌 {title[:100]}\n"
                       f"👤 {OWNER_USERNAME}"
            )
            await query.message.reply_text("✅ Thumbnail sent successfully!")
            
            async with aiosqlite.connect("bot_database.db") as db:
                await db.execute(
                    "INSERT INTO download_history (user_id, url, type) VALUES (?, ?, ?)",
                    (user_id, data['url'], 'thumbnail')
                )
                await db.commit()
            
        except Exception as e:
            await query.message.reply_text(f"❌ Failed to send thumbnail: {str(e)}")
    
    else:
        await query.message.reply_text(
            f"❌ Requested content not available!\n"
            f"💡 Try another download option."
        )

# ===================== ডাউনলোড হিস্টরি =====================
async def show_download_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ডাউনলোড হিস্টরি দেখায়"""
    user_id = update.effective_user.id
    
    async with aiosqlite.connect("bot_database.db") as db:
        async with db.execute(
            "SELECT url, type, download_time FROM download_history WHERE user_id = ? ORDER BY download_time DESC LIMIT 20",
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
    
    if not rows:
        await update.message.reply_text(
            "📊 **No Download History**\n\n"
            "You haven't downloaded anything yet.\n"
            "Start downloading now!",
            parse_mode="Markdown",
            reply_markup=get_downloader_keyboard()
        )
        return
    
    response = "📊 **My Download History**\n"
    response += "━" * 20 + "\n\n"
    
    for i, row in enumerate(rows, 1):
        url = row[0][:40] + "..." if len(row[0]) > 40 else row[0]
        media_type = row[1].capitalize()
        time = row[2][:16]
        response += f"{i}. {media_type} - {url}\n"
        response += f"   🕐 {time}\n\n"
    
    await update.message.reply_text(
        response,
        parse_mode="Markdown",
        reply_markup=get_downloader_keyboard()
    )

# ===================== বাকি ফাংশন (SMS, Bomber, ইত্যাদি) =====================
# এখানে আপনার আগের কোডের সব ফাংশন থাকবে
# process_sms_number, process_sms_message, process_bomber_number, 
# process_bomber_amount, show_profile, show_stats, process_redeem,
# handle_admin_commands, process_admin_states

# ... (আপনার আগের কোডের সব ফাংশন এখানে বসান) ...

# ===================== মেইন =====================
async def main():
    """বট চালু"""
    try:
        print("="*50)
        print("🤖 Starting Unified SMS Bot with Downloader...")
        print(f"Token: {BOT_TOKEN[:15]}...")
        print(f"👑 Admin ID: {ADMIN_ID}")
        
        # ডাটাবেস ইনিশিয়ালাইজ
        await init_db()
        
        # অ্যাপ্লিকেশন
        application = Application.builder().token(BOT_TOKEN).build()
        
        # হ্যান্ডলার
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(download_options_handler, pattern="^download_"))
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
