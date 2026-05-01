import os
import re
import sqlite3
from PIL import Image
import pytesseract
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# TOKEN ကို environment variable ကနေ ယူမယ်
TOKEN = os.getenv("BOT_TOKEN")

# DB Setup
conn = sqlite3.connect("data.db", check_same_thread=False)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS receipts (id TEXT PRIMARY KEY)")
conn.commit()

def exists_id(txid):
    cur.execute("SELECT id FROM receipts WHERE id=?", (txid,))
    return cur.fetchone() is not None

def save_id(txid):
    cur.execute("INSERT INTO receipts (id) VALUES (?)", (txid,))
    conn.commit()

def extract_txid(text):
    ids = re.findall(r'\d{8,}', text) # ၈ လုံးနှင့်အထက် ဂဏန်းများကို ရှာမည်
    return ids[0] if ids else None

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    
    path = "receipt.jpg"
    await file.download_to_drive(path)
    
    text = pytesseract.image_to_string(Image.open(path))
    txid = extract_txid(text)
    
    if not txid:
        return

    if exists_id(txid):
        await update.message.reply_text(f"⚠️ Duplicate ဖြစ်နေပါတယ်: {txid}")
    else:
        save_id(txid)
        await update.message.reply_text(f"✅ သိမ်းဆည်းပြီးပါပြီ ID: {txid}")

if __name__ == '__main__':
    if not TOKEN:
        print("Error: BOT_TOKEN not found in environment variables!")
    else:
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        print("Bot is running...")
        app.run_polling()
        
