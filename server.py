from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from yt_dlp import YoutubeDL
from shazamio import Shazam
import subprocess
import os
import asyncio

app = Flask(__name__)
BOT_TOKEN = "7780144299:AAEiGYayucjHGXMCxN0FPwDgjz7A-mTprko"  # ← TOKENNI BU YERGA YOPISHTIR

@app.route('/')
def home():
    return "Bot va Flask ishlayapti!"

def run_bot():
    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        for f in ["video.mp4", "audio.mp3", "music.mp3", "voice.ogg"]:
            if os.path.exists(f):
                os.remove(f)

        if "youtu" in text or "tiktok" in text or "instagram" in text:
            await update.message.reply_text("⏬ Videoni yuklab olyapman...")
            try:
                download_video(text)
                await context.bot.send_video(chat_id=update.effective_chat.id, video=open("video.mp4", 'rb'))

                await update.message.reply_text("🎧 Audio chiqarilmoqda...")
                extract_audio()
                await context.bot.send_audio(chat_id=update.effective_chat.id, audio=open("audio.mp3", 'rb'))
            except Exception as e:
                await update.message.reply_text(f"❌ Xatolik: {e}")
        else:
            await update.message.reply_text("🔍 Musiqa qidirilmoqda...")
            try:
                download_audio(text)
                await context.bot.send_audio(chat_id=update.effective_chat.id, audio=open("music.mp3", 'rb'))
            except Exception as e:
                await update.message.reply_text(f"❌ Xatolik: {e}")

    async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🎵 Musiqa aniqlanmoqda...")
        try:
            voice = await update.message.voice.get_file()
            await voice.download_to_drive("voice.ogg")

            # Convert ogg to mp3
            subprocess.run(["ffmpeg", "-i", "voice.ogg", "-y", "voice.mp3"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            shazam = Shazam()
            out = await shazam.recognize_song("voice.mp3")
            track = out.get("track", {})
            title = track.get("title", "Aniqlanmadi")
            subtitle = track.get("subtitle", "")

            await update.message.reply_text(f"🎧 Topildi: {title} - {subtitle}" if title != "Aniqlanmadi" else "❌ Musiqa aniqlanmadi.")
        except Exception as e:
            await update.message.reply_text(f"❌ Xatolik: {e}")

    def download_audio(query):
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'default_search': 'ytsearch',
            'outtmpl': 'music.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([query])

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
    app_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app_telegram.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app_telegram.run_polling()

Thread(target=run_bot).start()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)