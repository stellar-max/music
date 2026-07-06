# bot_handlers/play.py - /play command handler

import sqlite3
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from bot_config import config, logger

# Socket.IO reference (set from app.py)
socketio = None

def init_socketio(sio):
    """Initialize Socket.IO for broadcasting"""
    global socketio
    socketio = sio

async def play_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /play <song_name> - Play a song and broadcast to web"""
    if not context.args:
        await update.message.reply_text(
            config.PLAY_USAGE,
            parse_mode='Markdown'
        )
        return
    
    song_name = ' '.join(context.args)
    user = update.effective_user
    
    # Broadcast to web clients via Socket.IO
    if socketio:
        socketio.emit('telegram_play', {
            'song': song_name,
            'user': user.username or user.first_name,
            'user_id': user.id,
            'timestamp': datetime.now().isoformat()
        })
        logger.info(f"Broadcast play request: {song_name} from {user.username}")
    
    # Search in database
    conn = sqlite3.connect(config.DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Search by title or artist
    c.execute(
        "SELECT * FROM tracks WHERE title LIKE ? OR artist LIKE ? AND hidden = 0 LIMIT 5",
        (f"%{song_name}%", f"%{song_name}%")
    )
    results = c.fetchall()
    conn.close()
    
    if results:
        reply = f"🎵 **Search results for '{song_name}':**\n\n"
        for track in results:
            reply += f"• **{track['title']}** - {track['artist']}\n"
            reply += f"  🔗 /track/{track['id']}\n\n"
        reply += f"\n✅ Play request sent to web player!"
    else:
        reply = f"🎵 **Playing '{song_name}'...**\n\n"
        reply += f"🔊 Request sent to your web player!\n\n"
        reply += f"💡 *Tip: Make sure your web player is open to hear it.*\n"
        reply += f"🔗 {config.WEBAPP_URL}"
    
    await update.message.reply_text(reply, parse_mode='Markdown')
