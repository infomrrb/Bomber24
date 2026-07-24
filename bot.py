import logging
import requests
import json
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ===================== কনফিগারেশন =====================
TOKEN = "8919343304:AAEmHznQk2Q2tlkxNcOgTYDkMZZ5PesoBPw"
CHANNEL_USERNAME = "@VOTER_LIST_BANGLADESH"
API_URL = "https://apu-sand.vercel.app/send?number="
ADMIN_ID = 1967494059
OWNER_USERNAME = "@DARK_TUSHAR"

# ইউজার ডাটা স্টোর
user_data = {}
temp_data = {}

# ===================== লগিং =====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===================== চেক ফাংশন =====================
async def is_member(user_id, context):
    """চেক করে ইউজার চ্যানেলের মেম্বার কিনা"""
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# ===================== কীবোর্ড =====================
def get_main_keyboard():
    """মেইন মেনুর কীবোর্ড বাটন"""
    keyboard = [
        ["🚀 START BOMBER"],
        ["📊 MY INFO", "📞 CONTACT ADMIN"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_back_keyboard():
    """ব্যাক বাটন"""
    keyboard = [
        ["🔙 ব্যাক"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ===================== মেইন মেনু =====================
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """মেইন মেনু দেখায়"""
    user = update.effective_user
    
    # টেম্প ডাটা ক্লিয়ার
    if update.effective_user.id in temp_data:
        del temp_data[update.effective_user.id]
    
    await update.message.reply_text(
        f"🔥 ওয়েলকাম টু SMS BOMBER BOT 🔥\n\n"
        f"👤 ইউজার: {user.first_name}\n"
        f"🆔 আইডি: {user.id}\n\n"
        f"📌 নিচের বাটন থেকে অপশন সিলেক্ট করুন:",
        reply_markup=get_main_keyboard()
    )

# ===================== জয়েন বাটন =====================
async def join_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """জয়েন বাটন দেখায়"""
    keyboard = [
        [InlineKeyboardButton("📢 চ্যানেলে জয়েন করুন", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
        [InlineKeyboardButton("✅ চেক করুন", callback_data='check_join')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"⚠️ বট ব্যবহার করতে হলে আমাদের চ্যানেলে জয়েন করুন!\n\n"
        f"🔗 চ্যানেল: {CHANNEL_USERNAME}\n\n"
        f"জয়েন করার পর '✅ চেক করুন' বাটনে ক্লিক করুন।",
        reply_markup=reply_markup
    )

# ===================== স্টার্ট =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start কমান্ড হ্যান্ডলার"""
    user_id = update.effective_user.id
    
    # টেম্প ডাটা ক্লিয়ার
    if user_id in temp_data:
        del temp_data[user_id]
    
    # চেক করা ইউজার চ্যানেলের মেম্বার কিনা
    if await is_member(user_id, context):
        await main_menu(update, context)
    else:
        await join_button(update, context)

# ===================== ক্যালব্যাক হ্যান্ডলার =====================
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """বাটন ক্লিক হ্যান্ডলার"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # ===== CHECK JOIN =====
    if query.data == 'check_join':
        if await is_member(user_id, context):
            await query.message.delete()
            await context.bot.send_message(
                chat_id=user_id,
                text=f"✅ চ্যানেলে জয়েন করার জন্য ধন্যবাদ!\n\n🔥 ওয়েলকাম টু SMS BOMBER BOT 🔥\n\n📌 নিচের বাটন থেকে অপশন সিলেক্ট করুন:",
                reply_markup=get_main_keyboard()
            )
        else:
            await query.edit_message_text(
                f"❌ আপনি এখনও চ্যানেলে জয়েন করেননি!\n\n"
                f"🔗 চ্যানেল: {CHANNEL_USERNAME}\n\n"
                f"জয়েন করে '✅ চেক করুন' বাটনে ক্লিক করুন।"
            )

# ===================== মেসেজ হ্যান্ডলার =====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ইউজারের মেসেজ হ্যান্ডল করে"""
    user_id = update.effective_user.id
    message = update.message.text
    
    # চেক করা ইউজার চ্যানেলের মেম্বার কিনা
    if not await is_member(user_id, context):
        await join_button(update, context)
        return
    
    # ===== START BOMBER বাটন =====
    if message == "🚀 START BOMBER":
        temp_data[user_id] = {'step': 'awaiting_number'}
        
        await update.message.reply_text(
            f"📱 START BOMBER\n\n"
            f"দয়া করে টার্গেট নম্বর দিন:\n"
            f"উদাহরণ: 018XXXXXXXX\n\n"
            f"💡 শুধুমাত্র বাংলাদেশি নম্বর সমর্থিত",
            reply_markup=get_back_keyboard()
        )
        return
    
    # ===== MY INFO বাটন =====
    elif message == "📊 MY INFO":
        if user_id not in user_data:
            user_data[user_id] = {
                'total_bombing': 0,
                'total_success': 0,
                'total_failed': 0,
                'total_requests': 0
            }
        
        data = user_data[user_id]
        user = update.effective_user
        
        info_text = (
            f"📊 আমার তথ্য 📊\n\n"
            f"🆔 আইডি: {user.id}\n"
            f"👤 ইউজারনেম: @{user.username if user.username else 'N/A'}\n"
            f"📛 নাম: {user.first_name}\n\n"
            f"💣 মোট বোম্বিং: {data['total_bombing']}\n"
            f"📤 মোট রিকোয়েস্ট: {data['total_requests']}\n"
            f"✅ সফল: {data['total_success']}\n"
            f"❌ ব্যর্থ: {data['total_failed']}"
        )
        
        # সফলতার হার
        if data['total_requests'] > 0:
            success_rate = round((data['total_success'] / data['total_requests']) * 100, 2)
            info_text += f"\n📊 সফলতার হার: {success_rate}%"
        else:
            info_text += f"\n📊 সফলতার হার: 0%"
        
        await update.message.reply_text(
            info_text,
            reply_markup=get_main_keyboard()
        )
        return
    
    # ===== CONTACT ADMIN বাটন =====
    elif message == "📞 CONTACT ADMIN":
        admin_link = f"https://t.me/{OWNER_USERNAME.replace('@', '')}"
        
        await update.message.reply_text(
            f"📞 কন্ট্যাক্ট অ্যাডমিন\n\n"
            f"👨‍💻 অ্যাডমিন: {OWNER_USERNAME}\n\n"
            f"🔗 অ্যাডমিনকে মেসেজ করতে এই লিংকে ক্লিক করুন:\n"
            f"{admin_link}",
            reply_markup=get_main_keyboard()
        )
        return
    
    # ===== ব্যাক বাটন =====
    elif message == "🔙 ব্যাক":
        await main_menu(update, context)
        return
    
    # ===== টেম্প ডাটা চেক =====
    if user_id not in temp_data:
        await main_menu(update, context)
        return
    
    step = temp_data[user_id].get('step')
    
    # ===== নম্বর ইনপুট =====
    if step == 'awaiting_number':
        # চেক করা নম্বর ভ্যালিড কিনা
        if not message.isdigit() or len(message) < 11:
            await update.message.reply_text(
                f"❌ ভুল নম্বর!\n\n"
                f"দয়া করে সঠিক বাংলাদেশি নম্বর দিন।\n"
                f"উদাহরণ: 01859495889",
                reply_markup=get_back_keyboard()
            )
            return
        
        # নম্বর সেভ করে অ্যামাউন্ট চাই
        temp_data[user_id]['number'] = message
        temp_data[user_id]['step'] = 'awaiting_amount'
        
        await update.message.reply_text(
            f"✅ নম্বর সেট: {message}\n\n"
            f"💥 এখন অ্যামাউন্ট দিন (কতবার বোম্বিং হবে)\n\n"
            f"📌 উদাহরণ: 10, 20, 50\n"
            f"⚠️ ম্যাক্সিমাম: 100",
            reply_markup=get_back_keyboard()
        )
    
    # ===== অ্যামাউন্ট ইনপুট =====
    elif step == 'awaiting_amount':
        try:
            amount = int(message)
            if amount < 1 or amount > 100:
                await update.message.reply_text(
                    f"❌ অ্যামাউন্ট ১-১০০ এর মধ্যে হতে হবে!",
                    reply_markup=get_back_keyboard()
                )
                return
            
            number = temp_data[user_id]['number']
            
            # প্রক্রেসিং মেসেজ
            msg = await update.message.reply_text(
                f"⏳ বোম্বিং প্রক্রিয়াধীন...\n\n"
                f"📱 টার্গেট: {number}\n"
                f"💥 অ্যামাউন্ট: {amount}\n"
                f"⏰ দয়া করে অপেক্ষা করুন..."
            )
            
            # API কল
            success_count = 0
            failed_count = 0
            api_responses = []
            
            for i in range(amount):
                try:
                    api_response = requests.get(f"{API_URL}{number}", timeout=10)
                    response_data = api_response.json()
                    api_responses.append(response_data)
                    
                    # API রেসপন্স থেকে ডাটা নেওয়া
                    api_success = response_data.get('success', 0)
                    api_failed = response_data.get('failed', 0)
                    api_total = response_data.get('total_requests', 0)
                    api_amount = response_data.get('amount', 0)
                    
                    # সফল বা ব্যর্থ কাউন্ট
                    if api_success > 0:
                        success_count += api_success
                    else:
                        failed_count += 1
                        
                except Exception as e:
                    failed_count += 1
                    logger.error(f"API Error: {e}")
                
                # প্রতি ৫টি রিকোয়েস্টে আপডেট
                if (i + 1) % 5 == 0 or (i + 1) == amount:
                    try:
                        await msg.edit_text(
                            f"⏳ বোম্বিং চলছে...\n\n"
                            f"📱 টার্গেট: {number}\n"
                            f"✅ সফল: {success_count}\n"
                            f"❌ ব্যর্থ: {failed_count}\n"
                            f"📊 প্রগ্রেস: {i+1}/{amount}"
                        )
                    except:
                        pass
                
                # ছোট ডিলে
                time.sleep(0.3)
            
            # ইউজার ডাটা আপডেট
            if user_id not in user_data:
                user_data[user_id] = {
                    'total_bombing': 0,
                    'total_success': 0,
                    'total_failed': 0,
                    'total_requests': 0
                }
            
            user_data[user_id]['total_bombing'] += 1
            user_data[user_id]['total_success'] += success_count
            user_data[user_id]['total_failed'] += failed_count
            user_data[user_id]['total_requests'] += amount
            
            # সর্বশেষ API রেসপন্স থেকে তথ্য
            last_response = api_responses[-1] if api_responses else {}
            api_owner = last_response.get('Api_Owner', OWNER_USERNAME)
            api_amount = last_response.get('amount', amount)
            api_total = last_response.get('total_requests', amount)
            
            # সফলতার হার
            success_rate = round((success_count/amount)*100, 2) if amount > 0 else 0
            
            # রেসাল্ট মেসেজ (সবসময় সফল দেখাবে)
            result_message = (
                f"✅ বোম্বিং সফলভাবে সম্পন্ন! ✅\n\n"
                f"📱 টার্গেট: {number}\n"
                f"💥 অ্যামাউন্ট: {amount}\n"
                f"✅ সফল: {success_count}\n"
                f"❌ ব্যর্থ: {failed_count}\n"
                f"📊 সফলতার হার: {success_rate}%\n"
                f"📤 মোট রিকোয়েস্ট: {api_total}\n\n"
                f"👨‍💻 API Owner: {api_owner}\n\n"
                f"📌 আপনার মোট বোম্বিং: {user_data[user_id]['total_bombing']}"
            )
            
            # রেসাল্ট দেখান
            await msg.edit_text(result_message)
            
            # মেইন মেনু দেখান
            await update.message.reply_text(
                f"🏠 মেইন মেনুতে ফিরে আসুন",
                reply_markup=get_main_keyboard()
            )
            
            # টেম্প ডাটা ক্লিয়ার
            if user_id in temp_data:
                del temp_data[user_id]
            
        except ValueError:
            await update.message.reply_text(
                f"❌ ভুল ইনপুট!\n\n"
                f"দয়া করে একটি সংখ্যা দিন।\n"
                f"উদাহরণ: 10, 20, 50",
                reply_markup=get_back_keyboard()
            )
        except Exception as e:
            await update.message.reply_text(
                f"❌ এরর!\n\n"
                f"সমস্যা: {str(e)}\n\n"
                f"আবার চেষ্টা করুন।",
                reply_markup=get_main_keyboard()
            )
            if user_id in temp_data:
                del temp_data[user_id]

# ===================== মেইন ফাংশন =====================
def main():
    """বট চালু করে"""
    application = Application.builder().token(TOKEN).build()
    
    # কমান্ড হ্যান্ডলার
    application.add_handler(CommandHandler("start", start))
    
    # মেসেজ হ্যান্ডলার
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # ক্যালব্যাক হ্যান্ডলার
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # বট চালু
    print("="*50)
    print("🤖 SMS BOMBER BOT চালু হচ্ছে...")
    print(f"📢 চ্যানেল: {CHANNEL_USERNAME}")
    print(f"👨‍💻 অ্যাডমিন: {OWNER_USERNAME}")
    print("✅ বট সম্পূর্ণ রেডি!")
    print("="*50)
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
