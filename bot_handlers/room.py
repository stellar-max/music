# bot_handlers/room.py - /room command handler

import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot_config import config, logger

async def room_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /room - Room management"""
    keyboard = [
        [InlineKeyboardButton("📋 List Rooms", callback_data="list_rooms")],
        [InlineKeyboardButton("➕ Create Room", callback_data="create_room")],
        [InlineKeyboardButton("🔗 Join Room", callback_data="join_room")],
        [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_rooms")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Get active rooms count
    conn = sqlite3.connect(config.DB_FILE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM rooms")
    room_count = c.fetchone()[0]
    conn.close()
    
    await update.message.reply_text(
        f"{config.ROOM_TEXT}\n\n"
        f"📊 **Active Rooms:** {room_count}\n"
        f"🌐 **Web Player:** {config.WEBAPP_URL}",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    logger.info(f"User {update.effective_user.username} accessed room management")
