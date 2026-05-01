import os
import re
import sqlite3
import hashlib
from PIL import Image
import pytesseract

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

# --- DB setup ---
conn = sqlite3.connect("data.db", check_same_thread=False)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS receipts (
    id TEXT PRIMARY KEY
)
""")
conn.commit()

def save_id(txid):
    try:
        cur.execute("INSERT INTO receipts (id) VALUES (?)", (txid,))
        conn.commit()
        return True
    except:
        return False

def exists_id(txid):
    cur.execute("SELECT id FROM receipts WHERE id=?", (txid,))
    return cur.fetchone() is not None

# --- OCR ---
def extract_text(path):
    return pytesseract.image_to_string(Image.open(path))

def extract_txid(text):
    ids = re.findall(r'\d{8,}', text)
    return ids[0] if ids else None

def extract_amount(text):
    amounts = re.findall(r'\d{1,3}(?:,\d{3})+', text)
    return amounts[0] if amounts else None

# --- Handler ---
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()

    path = "receipt.jpg"
    await file.download_to_drive(path)

    text = extract_text(path)

    txid = extract_txid(text)
    amount = extract_amount(text)

    if not txid:
        return  # silent

    if exists_id(txid):
        await update.message.reply_text("⚠️ ဒီပြေစာက အရင်တင်ပြီးသားပါ")
    else:
        save_id(txid)
        # optional reply
        # await update.message.reply_text(f"✅ OK\nID: {txid}\nAmount: {amount}")

# --- Run ---
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

print("Bot running...")
app.run_polling()
