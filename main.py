import os
import subprocess
import tempfile
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# YENİ TOKENİNİ TIRNAK İÇİNE YAZ
TOKEN = "8090764217:AAHeGwTajkYyux_9uzsxFzGuqW1qwQ1XuEo" 

# --- RENDER AYAKTA TUTMA KODU ---
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Bot calisiyor!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host="0.0.0.0", port=port)

# --- BOT KODLARI ---
async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.audio or update.message.voice or update.message.video or update.message.document
    if not file: return

    tg_file = await file.get_file()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as in_file:
        input_path = in_file.name
    with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as out_file:
        output_path = out_file.name

    try:
        await tg_file.download_to_drive(input_path)
        subprocess.run(["ffmpeg", "-y", "-i", input_path, "-c:a", "libopus", "-b:a", "64k", "-ar", "48000", "-ac", "1", output_path], check=True)
        with open(output_path, "rb") as f: await update.message.reply_voice(f)
    except Exception as e:
        await update.message.reply_text(f"Hata: {e}")
    finally:
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)

if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.AUDIO | filters.VOICE | filters.VIDEO | filters.Document.ALL, handle_audio))
    app.run_polling()
    
