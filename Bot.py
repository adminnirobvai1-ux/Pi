import os
import time
import telebot
from telebot import types
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options

# রিমোট ডেস্কটপ ডিসপ্লে সেট করা (যাতে noVNC-তে দেখা যায়)
os.environ["DISPLAY"] = ":1"

BOT_TOKEN = "8955426078:AAFpjgYEYHDyNJ2dJhqZ5S4e4qzINulz5js"
TARGET_URL = "https://dkwin0.com/#/login"

bot = telebot.TeleBot(BOT_TOKEN)
user_sessions = {}

# ১. /start কমান্ড হ্যান্ডলার
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_dk = types.InlineKeyboardButton("🔥 DK Win Login", callback_data="site_dkwin")
    markup.add(btn_dk)
    
    bot.reply_to(
        message, 
        "👋 **স্বাগতম Dark Killer Automation প্যানেলে!**\n\nকাজ শুরু করতে নিচের সাইট বাটনে ক্লিক করুন:",
        parse_mode="Markdown",
        reply_markup=markup
    )

# ২. বাটন ক্লিক হ্যান্ডলার
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    if call.data == "site_dkwin":
        user_sessions[chat_id] = {}
        msg = bot.send_message(chat_id, "📱 আপনার **মোবাইল নম্বর** (N) লিখে পাঠান:")
        bot.register_next_step_handler(msg, process_phone_step)

# ৩. মোবাইল নম্বর গ্রহণ
def process_phone_step(message):
    chat_id = message.chat.id
    phone = message.text.strip()
    user_sessions[chat_id]['phone'] = phone
    
    msg = bot.send_message(chat_id, "🔑 এবার আপনার **পাসওয়ার্ড** (P) লিখে পাঠান:")
    bot.register_next_step_handler(msg, process_password_step)

# ৪. পাসওয়ার্ড গ্রহণ এবং সেলেনিয়াম অটোমেশন চালু
def process_password_step(message):
    chat_id = message.chat.id
    password = message.text.strip()
    user_sessions[chat_id]['password'] = password
    
    bot.send_message(chat_id, "⏳ **ব্রাউজার শুরু হচ্ছে...** তথ্য টাইপ করা হচ্ছে। দয়া করে অপেক্ষা করুন।")
    
    phone = user_sessions[chat_id]['phone']
    run_selenium_login(chat_id, phone, password)

# ৫. সেলেনিয়াম অটোমেশন ফাংশন
def run_selenium_login(chat_id, phone, password):
    driver = None
    try:
        options = Options()
        # ডিসপ্লেতে ব্রাউজার সরাসরি দৃশ্যমান হবে
        driver = webdriver.Firefox(options=options)
        driver.maximize_window()
        
        # টার্গেট সাইট ওপেন
        driver.get(TARGET_URL)
        wait = WebDriverWait(driver, 20)

        # ১. নম্বর ফিল্ড (N) সিলেক্টর
        phone_selector = "body > div > div:nth-of-type(2) > div:nth-of-type(4) > div > div > div > div:nth-of-type(2) > input"
        phone_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, phone_selector)))
        phone_input.clear()
        phone_input.send_keys(phone)
        time.sleep(1)

        # ২. পাসওয়ার্ড ফিল্ড (P) সিলেক্টর
        pass_selector = "body > div > div:nth-of-type(2) > div:nth-of-type(4) > div > div > div:nth-of-type(2) > div:nth-of-type(2) > input"
        pass_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, pass_selector)))
        pass_input.clear()
        pass_input.send_keys(password)
        time.sleep(1)

        # ৩. লগইন বাটন (L) সিলেক্টর
        login_btn_selector = "body > div > div:nth-of-type(2) > div:nth-of-type(4) > div > div > div:nth-of-type(4) > button"
        login_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, login_btn_selector)))
        login_btn.click()

        time.sleep(4)
        
        # সফলতার প্রমাণস্বরূপ স্ক্রিনশট নেওয়া ও টেলিগ্রামে পাঠানো
        screenshot_path = f"/tmp/login_{chat_id}.png"
        driver.save_screenshot(screenshot_path)
        with open(screenshot_path, 'rb') as photo:
            bot.send_photo(chat_id, photo, caption="✅ **লগইন রিকোয়েস্ট সফলভাবে সম্পন্ন হয়েছে!**")
        
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)

    except Exception as e:
        bot.send_message(chat_id, f"❌ **কোনো একটি সমস্যা হয়েছে:**\n`{str(e)}`", parse_mode="Markdown")

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
