from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler
from yt_dlp import YoutubeDL
from shazamio import Shazam
import subprocess
import os
import asyncio

BOT_TOKEN = "7780144299:AAEiGYayucjHGXMCxN0FPwDgjz7A-mTprko" ADMIN_ID = 2097478310 CHANNEL_USERNAME = "@AFSUNGAR_MERLIN_SERIALI_K"

app = Flask(name) music_results = {}

@app.route('/') def home(): return "Bot va Flask ishlayapti!"

def run_bot(): async def is_subscribed(user_id): try: member = await app_telegram.bot.get_chat_member(CHANNEL_USERNAME, user_id) return member.status in ["member", "creator", "administrator"] except: return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    register_user(user_id)

    if not await is_subscribed(user_id):
        btn = [[InlineKeyboardButton("🔗 Kanalga obuna bo‘lish", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
               [InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_sub")]]
        await update.message.reply_text("❗ Botdan foydalanish uchun kanalga obuna bo‘ling:", reply_markup=InlineKeyboardMarkup(btn))
        return

    await update.message.reply_text("👋 Salom! Musiqa nomini yoki linkni yuboring.")

async def check_sub_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if await is_subscribed(user_id):
        await query.edit_message_text("✅ Obuna tasdiqlandi! Endi botdan foydalanishingiz mumkin.")
    else:
        await query.edit_message_text("❌ Hali ham obuna emassiz. Avval kanalga qo‘shiling.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    register_user(user_id)

    if not await is_subscribed(user_id):
        btn = [[InlineKeyboardButton("🔗 Kanalga obuna bo‘lish", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
               [InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_sub")]]
        await update.message.reply_text("❗ Iltimos, avval kanalga obuna bo‘ling.", reply_markup=InlineKeyboardMarkup(btn))
        return

    text = update.message.text
    if "youtu" in text or "tiktok" in text or "instagram" in text:
        await update.message.reply_text("⏬ Videoni yuklab olyapman...")
        try:
            download_video(text)
            await context.bot.send_video(chat_id=update.effective_chat.id, video=open("video.mp4", 'rb'))
            await update.message.reply_text("🎧 Audio chiqarilmoqda...")
            extract_audio()
            btns = [[InlineKeyboardButton("🎬 YouTube'da ochish", url=text)]]
            await context.bot.send_audio(chat_id=update.effective_chat.id, audio=open("audio.mp3", 'rb'), reply_markup=InlineKeyboardMarkup(btns))
        except Exception as e:
            await update.message.reply_text(f"❌ Xatolik: {e}")
    else:
        await update.message.reply_text("🔍 Musiqa natijalari topilmoqda...")
        try:
            results = search_music_list(text)
            if not results:
                await update.message.reply_text("❌ Hech narsa topilmadi.")
                return
            music_results[user_id] = results
            buttons = [[InlineKeyboardButton(f"🎵 {title}", callback_data=f"music_{i}")] for i, (title, url) in enumerate(results)]
            await update.message.reply_text("🎧 Tanlang:", reply_markup=InlineKeyboardMarkup(buttons))
        except Exception as e:
            await update.message.reply_text(f"❌ Xatolik: {e}")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    register_user(user_id)

    if not await is_subscribed(user_id):
        btn = [[InlineKeyboardButton("🔗 Kanalga obuna bo‘lish", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
               [InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_sub")]]
        await update.message.reply_text("❗ Avval kanalga obuna bo‘ling.", reply_markup=InlineKeyboardMarkup(btn))
        return

    await update.message.reply_text("🎵 Musiqa aniqlanmoqda...")
    try:
        voice = await update.message.voice.get_file()
        await voice.download_to_drive("voice.ogg")
        subprocess.run(["ffmpeg", "-i", "voice.ogg", "-y", "voice.mp3"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        shazam = Shazam()
        out = await shazam.recognize_song("voice.mp3")
        track = out.get("track", {})
        title = track.get("title", "Aniqlanmadi")
        subtitle = track.get("subtitle", "")
        await update.message.reply_text(f"🎧 Topildi: {title} - {subtitle}" if title != "Aniqlanmadi" else "❌ Musiqa aniqlanmadi.")
    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik: {e}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "check_sub":
        if await is_subscribed(user_id):
            await query.edit_message_text("✅ Obuna tasdiqlandi!")
        else:
            await query.edit_message_text("❌ Hali ham obuna emassiz.")
    elif data.startswith("music_"):
        index = int(data.split("_")[1])
        results = music_results.get(user_id, [])
        if index < len(results):
            _, url = results[index]
            await query.edit_message_text("⏬ Yuklab olinmoqda...")
            download_selected_music(url)
            await context.bot.send_audio(chat_id=query.message.chat.id, audio=open("music.mp3", 'rb'))

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    users = load_users()
    await update.message.reply_text(f"👤 Foydalanuvchilar soni: {len(users)}\n✉️ Xabar yuborish uchun /send <xabar>")

async def send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    text = " ".join(context.args)
    users = load_users()
    for uid in users:
        try:
            await context.bot.send_message(chat_id=uid, text=text)
        except:
            pass
    await update.message.reply_text("✅ Xabar yuborildi.")

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
        'outtmpl': 'music.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def download_video(url):
    ydl_opts = {
        'format': 'best[ext=mp4]',
        'outtmpl': 'video.%(ext)s',
        'quiet': True
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def extract_audio():
    subprocess.run(["ffmpeg", "-i", "video.mp4", "-vn", "-acodec", "libmp3lame", "-y", "audio.mp3"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

app_telegram = ApplicationBuilder().token(BOT_TOKEN).build()
app_telegram.add_handler(CommandHandler("start", start))
app_telegram.add_handler(CommandHandler("admin", admin))
app_telegram.add_handler(CommandHandler("send", send_broadcast))
app_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app_telegram.add_handler(MessageHandler(filters.VOICE, handle_voice))
app_telegram.add_handler(CallbackQueryHandler(handle_callback))
app_telegram.run_polling()

Thread(target=run_bot).start()

if name == 'main': app.run(host="0.0.0.0", port=10000)

