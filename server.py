from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackQueryHandler
)
from yt_dlp import YoutubeDL
from shazamio import Shazam
import subprocess
import os
import asyncio

BOT_TOKEN = "7780144299:AAEiGYayucjHGXMCxN0FPwDgjz7A-mTprko" ADMIN_ID = 2097478310 CHANNEL_USERNAME = "@AFSUNGAR_MERLIN_SERIALI_K"

app = Flask(name) music_results = {}

@app.route('/') def home(): return "Bot ishlayapti!"

def run_bot(): async def is_subscribed(user_id): try: member = await application.bot.get_chat_member(CHANNEL_USERNAME, user_id) return member.status in ["member", "administrator", "creator"] except: return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    register_user(user_id)

    if not await is_subscribed(user_id):
        btn = [
            [InlineKeyboardButton("🔗 Obuna bo‘lish", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_sub")]
        ]
        await update.message.reply_text("❗ Botdan foydalanish uchun kanalga obuna bo‘ling:", reply_markup=InlineKeyboardMarkup(btn))
        return

    await update.message.reply_text("👋 Salom! Musiqa nomi, ovozi yoki link yuboring.")

async def check_sub_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if await is_subscribed(user_id):
        await query.edit_message_text("✅ Obuna tasdiqlandi! Botdan foydalanishingiz mumkin.")
    else:
        await query.edit_message_text("❌ Hali ham obuna emassiz.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    register_user(user_id)

    if not await is_subscribed(user_id):
        btn = [
            [InlineKeyboardButton("🔗 Obuna bo‘lish", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_sub")]
        ]
        await update.message.reply_text("❗ Kanalga obuna bo‘ling.", reply_markup=InlineKeyboardMarkup(btn))
        return

    if any(link in text for link in ["youtube.com", "youtu.be", "tiktok.com", "instagram.com"]):
        await update.message.reply_text("⏬ Video yuklanmoqda...")
        try:
            download_video(text)
            await context.bot.send_video(chat_id=update.effective_chat.id, video=open("video.mp4", 'rb'))
            await update.message.reply_text("🎧 Audio chiqarilmoqda...")
            extract_audio()
            await context.bot.send_audio(chat_id=update.effective_chat.id, audio=open("audio.mp3", 'rb'))
        except Exception as e:
            await update.message.reply_text(f"Xatolik: {e}")
    else:
        await update.message.reply_text("🔍 Musiqa qidirilmoqda...")
        try:
            results = search_music_list(text)
            if not results:
                await update.message.reply_text("Hech narsa topilmadi.")
                return
            music_results[user_id] = results
            buttons = [[InlineKeyboardButton(title, callback_data=f"music_{i}")] for i, (title, url) in enumerate(results)]
            await update.message.reply_text("Tanlang:", reply_markup=InlineKeyboardMarkup(buttons))
        except Exception as e:
            await update.message.reply_text(f"Xatolik: {e}")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    register_user(user_id)

    if not await is_subscribed(user_id):
        await update.message.reply_text("❗ Avval kanalga obuna bo‘ling.")
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
        await update.message.reply_text(f"Topildi: {title} - {subtitle}" if title != "Aniqlanmadi" else "❌ Aniqlanmadi")
    except Exception as e:
        await update.message.reply_text(f"Xatolik: {e}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "check_sub":
        if await is_subscribed(user_id):
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

application = ApplicationBuilder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(handle_callback))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
application.add_handler(MessageHandler(filters.VOICE, handle_voice))
application.run_polling()

Thread(target=run_bot).start()

if name == "main": app.run(host="0.0.0.0", port=10000)

