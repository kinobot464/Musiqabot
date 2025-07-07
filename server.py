from flask import Flask
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from yt_dlp import YoutubeDL
from shazamio import Shazam
import subprocess, os, asyncio
from threading import Thread

BOT_TOKEN = "7740266168:AAHVUXz-dp2P8gADtq4QJmXGoVVHv7zejcs"
CHANNEL_USERNAME = "@AFSUNGAR_MERLIN_SERIALI_K"
music_results = {}

app = Flask(__name__)

@app.route('/')
def index():
    return "Bot ishlayapti!"

# === Yordamchi funksiyalar ===

def register_user(user_id):
    users = load_users()
    if str(user_id) not in users:
        with open("users.txt", "a") as f:
            f.write(f"{user_id}\n")

def load_users():
    if not os.path.exists("users.txt"):
        return []
    with open("users.txt") as f:
        return f.read().splitlines()

async def is_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

def search_music_list(query):
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'extract_flat': 'in_playlist',
        'default_search': 'ytsearch10'
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        return [(entry.get("title"), entry.get("url")) for entry in info.get("entries", [])]

def download_selected_music(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'music.mp3',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

# === Telegram handlerlar ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    register_user(user_id)
    if not await is_subscribed(context.bot, user_id):
        btn = [
            [InlineKeyboardButton("🔗 Obuna bo‘lish", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_sub")]
        ]
        await update.message.reply_text("❗ Botdan foydalanish uchun kanalga obuna bo‘ling:", reply_markup=InlineKeyboardMarkup(btn))
        return
    await update.message.reply_text("👋 Salom! Musiqa nomi yoki link yuboring.")

async def check_sub_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if await is_subscribed(context.bot, user_id):
        await query.edit_message_text("✅ Obuna tasdiqlandi!")
    else:
        await query.edit_message_text("❌ Hali ham obuna emassiz.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    register_user(user_id)
    if not await is_subscribed(context.bot, user_id):
        btn = [
            [InlineKeyboardButton("🔗 Obuna bo‘lish", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_sub")]
        ]
        await update.message.reply_text("❗ Kanalga obuna bo‘ling.", reply_markup=InlineKeyboardMarkup(btn))
        return
    await update.message.reply_text("🔍 Musiqa qidirilmoqda...")
    try:
        results = search_music_list(text)
        if not results:
            await update.message.reply_text("Hech narsa topilmadi.")
            return
        music_results[user_id] = results
        buttons = [[InlineKeyboardButton(title, callback_data=f"music_{i}")] for i, (title, _) in enumerate(results)]
        await update.message.reply_text("Tanlang:", reply_markup=InlineKeyboardMarkup(buttons))
    except Exception as e:
        await update.message.reply_text(f"Xatolik: {e}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    if data == "check_sub":
        if await is_subscribed(context.bot, user_id):
            await query.edit_message_text("✅ Obuna tasdiqlandi!")
        else:
            await query.edit_message_text("❌ Obuna topilmadi.")
    elif data.startswith("music_"):
        index = int(data.split("_")[1])
        results = music_results.get(user_id, [])
        if index < len(results):
            _, url = results[index]
            await query.edit_message_text("⏬ Yuklab olinmoqda...")
            download_selected_music(url)
            await context.bot.send_audio(chat_id=query.message.chat.id, audio=open("music.mp3", 'rb'))

# === Flaskni ishga tushiramiz ===
def start_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# === Telegram botni ishga tushiramiz ===
async def run_bot():
    app_telegram = ApplicationBuilder().token(BOT_TOKEN).build()
    app_telegram.add_handler(CommandHandler("start", start))
    app_telegram.add_handler(CallbackQueryHandler(handle_callback))
    app_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    await app_telegram.run_polling()

# === Ikkalasini parallel ishlatamiz ===
if __name__ == "__main__":
    Thread(target=start_flask).start()
    asyncio.run(run_bot())