import asyncio
import logging
import time
import requests
import aiosqlite
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ===================== কনফিগারেশন =====================
BOT_TOKEN = "8826486988:AAFOOfdcrVCgvj532plzOQUXwx40yn3USl0"
ADMIN_ID = 1967494059
CHANNEL_USERNAME = "@VOTER_LIST_BANGLADESH"

# ===================== লগিং =====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG  # DEBUG লেভেল দেখাবে সব
)
logger = logging.getLogger(__name__)

# ===================== স্টার্ট =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """সরল স্টার্ট কমান্ড"""
    user = update.effective_user
    logger.info(f"Start command from {user.id}")
    
    keyboard = [
        ["📨 Send SMS", "💣 SMS Bomber"],
        ["👤 My Profile", "🎁 Redeem Code"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        f"🔥 Welcome {user.first_name}!\n\nBot is working!",
        reply_markup=reply_markup
    )

# ===================== মেসেজ হ্যান্ডলার =====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """মেসেজ হ্যান্ডলার"""
    user_id = update.effective_user.id
    message = update.message.text
    logger.info(f"Message from {user_id}: {message}")
    
    if message == "📨 Send SMS":
        await update.message.reply_text("📱 Enter phone number:")
        context.user_data['step'] = 'sms_number'
        return
    
    elif message == "💣 SMS Bomber":
        await update.message.reply_text("💣 Enter target number:")
        context.user_data['step'] = 'bomber_number'
        return
    
    elif message == "👤 My Profile":
        await update.message.reply_text(f"👤 Your ID: {user_id}")
        return
    
    elif message == "🎁 Redeem Code":
        await update.message.reply_text("🎟 Enter redeem code:")
        context.user_data['step'] = 'redeem'
        return
    
    # স্টেপ অনুযায়ী
    if context.user_data.get('step') == 'sms_number':
        await update.message.reply_text(f"✅ Number saved: {message}\nNow enter message:")
        context.user_data['step'] = 'sms_message'
        context.user_data['number'] = message
    
    elif context.user_data.get('step') == 'sms_message':
        await update.message.reply_text(f"✅ Sending SMS to {context.user_data.get('number')}...")
        # এখানে SMS API কল
        context.user_data.clear()
    
    elif context.user_data.get('step') == 'bomber_number':
        await update.message.reply_text(f"✅ Target: {message}\nEnter amount (1-100):")
        context.user_data['step'] = 'bomber_amount'
        context.user_data['number'] = message
    
    elif context.user_data.get('step') == 'bomber_amount':
        try:
            amount = int(message)
            await update.message.reply_text(f"💥 Bombing {amount} times to {context.user_data.get('number')}...")
            # এখানে Bomber API কল
            context.user_data.clear()
        except:
            await update.message.reply_text("❌ Enter a valid number!")
    
    elif context.user_data.get('step') == 'redeem':
        await update.message.reply_text(f"🎟 Redeeming code: {message}")
        context.user_data.clear()
    
    else:
        await update.message.reply_text("❌ Use the buttons below:")

# ===================== মেইন =====================
async def main():
    """বট চালু"""
    try:
        # টোকেন চেক
        if not BOT_TOKEN:
            print("❌ BOT_TOKEN is empty!")
            return
        
        print("="*50)
        print("🤖 Bot starting...")
        print(f"Token: {BOT_TOKEN[:10]}...")
        
        # অ্যাপ্লিকেশন বিল্ড
        application = Application.builder().token(BOT_TOKEN).build()
        
        # হ্যান্ডলার
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        print("✅ Bot is ready!")
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

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⛔ Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
