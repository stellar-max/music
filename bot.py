# bot.py - Clean Telegram Bot with Socket.IO integration
# Handles authentication, room management, and playback control

import os
import sqlite3
import logging
import uuid
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import sys
import threading
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from bot_config import BOT_TOKEN, WEBAPP_URL, DB_FILE, logger, socketio
from bot_handlers import (
    start_command,
    login_command,
    play_command,
    room_command,
    help_command,
    button_callback
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

WEBAPP_URL = os.environ.get('WEBAPP_URL', 'https://swagplayer.onrender.com')
DB_FILE = 'music.db'

# Socket.IO reference (set from app.py)
socketio = None

# ============================================================================
# TELEGRAM BOT (run in background)
# ============================================================================

def start_bot():
    """Start the Telegram bot in a background thread"""
    import threading
    from bot import run_bot
    
    def bot_thread():
        try:
            run_bot(socketio)
        except Exception as e:
            print(f"Bot error: {e}")
    
    thread = threading.Thread(target=bot_thread, daemon=True)
    thread.start()
    print("🤖 Telegram bot thread started")

# Uncomment this line to start the bot automatically
# start_bot()

# ============================================================================
# DATABASE HELPERS
# ============================================================================

def get_db_connection():
    """Get SQLite database connection"""
    return sqlite3.connect(DB_FILE)

def create_auth_token(telegram_id: int) -> str:
    """Create a short-lived authentication token"""
    token = str(uuid.uuid4()).replace('-', '')[:32]
    expires_at = datetime.now() + timedelta(minutes=10)
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO auth_tokens (token, telegram_id, expires_at) VALUES (?, ?, ?)",
        (token, telegram_id, expires_at.isoformat())
    )
    conn.commit()
    conn.close()
    return token

def get_user_by_telegram_id(telegram_id: int):
    """Get user from database by Telegram ID"""
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    user = c.fetchone()
    conn.close()
    return dict(user) if user else None

def create_user(telegram_id: int, username: str, first_name: str, last_name: str = ''):
    """Create a new user in database"""
    display_name = first_name
    if last_name:
        display_name += f" {last_name}"
    nickname = username if username else f"user_{telegram_id}"
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        """INSERT INTO users (telegram_id, username, first_name, last_name, display_name, nickname)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (telegram_id, username, first_name, last_name, display_name, nickname)
    )
    conn.commit()
    user_id = c.lastrowid
    conn.close()
    return user_id

# ============================================================================
# BOT HANDLERS
# ============================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command - Welcome user and provide login link"""
    user = update.effective_user
    telegram_id = user.id
    
    # Check if user exists, if not create them
    existing = get_user_by_telegram_id(telegram_id)
    if not existing:
        create_user(telegram_id, user.username, user.first_name, user.last_name)
    
    # Create login token
    token = create_auth_token(telegram_id)
    login_url = f"{WEBAPP_URL}/auth/browser/{token}"
    
    keyboard = [
        [InlineKeyboardButton("🎵 Open Web Player", url=login_url)],
        [InlineKeyboardButton("📱 Open in App", url=f"{WEBAPP_URL}/app")],
        [InlineKeyboardButton("👥 Create Room", callback_data="create_room")],
        [InlineKeyboardButton("🎧 My Library", callback_data="my_library")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = f"""
🎵 **Welcome to swagPlayer, {user.first_name}!**

Your personal music streaming hub with:
• 🎤 **Synced LRC Lyrics**
• 📀 **Album & Playlist Management**
• 👥 **Collaborative Rooms**
• 📱 **Telegram Integration**

🔑 **Click below to open the web player and start listening!**
    """
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    logger.info(f"User {user.username} ({telegram_id}) started bot")

async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /login - Generate a new login link"""
    user = update.effective_user
    token = create_auth_token(user.id)
    login_url = f"{WEBAPP_URL}/auth/browser/{token}"
    
    keyboard = [[InlineKeyboardButton("🔑 Login to Web Player", url=login_url)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🔑 **Your login link is ready!**\n\n"
        f"Click the button below to log in to the web player.\n\n"
        f"⏰ This link expires in 10 minutes.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def play_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /play <song_name> - Play a song and broadcast to web"""
    if not context.args:
        await update.message.reply_text(
            "🎵 **Usage:** `/play <song name>`\n\n"
            "Example: `/play Bohemian Rhapsody`",
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
    
    # Also search in database
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(
        "SELECT * FROM tracks WHERE title LIKE ? AND hidden = 0 LIMIT 5",
        (f"%{song_name}%",)
    )
    results = c.fetchall()
    conn.close()
    
    if results:
        reply = f"🎵 **Search results for '{song_name}':**\n\n"
        for track in results:
            reply += f"• {track['artist']} - {track['title']}\n"
        reply += f"\n✅ Play request sent to web player!"
    else:
        reply = f"🎵 **Playing '{song_name}'...**\n\n"
        reply += f"🔊 Request sent to your web player!\n\n"
        reply += f"💡 *Tip: Make sure your web player is open to hear it.*"
    
    await update.message.reply_text(reply, parse_mode='Markdown')

async def room_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /room - Room management"""
    keyboard = [
        [InlineKeyboardButton("📋 List Rooms", callback_data="list_rooms")],
        [InlineKeyboardButton("➕ Create Room", callback_data="create_room")],
        [InlineKeyboardButton("🔗 Join Room", callback_data="join_room")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🎧 **Room Management**\n\n"
        "Create or join collaborative listening rooms to enjoy music together!",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help - Show help message"""
    help_text = """
🤖 **swagPlayer Bot Help**

**Commands:**
• `/start` - Welcome and login
• `/login` - Get web player login link
• `/play <song>` - Play a song on your web player
• `/room` - Manage collaborative rooms
• `/help` - Show this help

**Features:**
• 🎵 **Web Player** - Stream your music with synced lyrics
• 👥 **Rooms** - Listen together with friends in real-time
• 📱 **Telegram Integration** - Control playback from your phone

🔗 **Web Player:** {WEBAPP_URL}
    """.format(WEBAPP_URL=WEBAPP_URL)
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

# ============================================================================
# CALLBACK HANDLERS
# ============================================================================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline keyboard button presses"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user = query.from_user
    
    if data == "create_room":
        # Generate room creation link
        room_url = f"{WEBAPP_URL}/rooms"
        keyboard = [[InlineKeyboardButton("🎧 Open Room", url=room_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🎧 **Create a Room**\n\n"
            "Click below to open the web player and create a collaborative room.\n\n"
            "Share the room link with friends to listen together!",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif data == "list_rooms":
        # Get active rooms
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("""
            SELECT r.*, COUNT(rm.id) as member_count, u.display_name as host_name
            FROM rooms r
            JOIN users u ON r.host_id = u.id
            LEFT JOIN room_members rm ON r.id = rm.room_id
            GROUP BY r.id
            ORDER BY r.created_at DESC
            LIMIT 5
        """)
        rooms = c.fetchall()
        conn.close()
        
        if rooms:
            reply = "📋 **Active Rooms**\n\n"
            for room in rooms:
                reply += f"• **{room['name']}** - {room['member_count']} members\n"
                reply += f"  Host: {room['host_name']}\n"
                reply += f"  Link: {WEBAPP_URL}/room/{room['id']}\n\n"
            reply += "\n💡 Click a link above to join a room!"
        else:
            reply = "📋 **No active rooms**\n\nBe the first to create one!"
        
        keyboard = [[InlineKeyboardButton("🔄 Refresh", callback_data="list_rooms")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            reply,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif data == "join_room":
        await query.edit_message_text(
            "🔗 **Join a Room**\n\n"
            "1. Open the web player: {WEBAPP_URL}\n"
            "2. Go to 'Rooms'\n"
            "3. Click 'Join Room' and enter the room ID\n\n"
            "Or use a direct link: {WEBAPP_URL}/room/<room_id>".format(WEBAPP_URL=WEBAPP_URL),
            parse_mode='Markdown'
        )
    
    elif data == "my_library":
        user_db = get_user_by_telegram_id(user.id)
        if user_db:
            library_url = f"{WEBAPP_URL}/user/{user_db['nickname']}"
            keyboard = [[InlineKeyboardButton("📚 Open Library", url=library_url)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "📚 **Your Library**\n\n"
                "Click below to view your uploaded tracks and albums!",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text("User not found. Please use /start first.")

# ============================================================================
# BOT INITIALIZATION
# ============================================================================

def init_bot(socketio_instance=None):
    """Initialize the bot with Socket.IO instance"""
    global socketio
    socketio = socketio_instance
    
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not set! Bot will not start.")
        return None
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("login", login_command))
    application.add_handler(CommandHandler("play", play_command))
    application.add_handler(CommandHandler("room", room_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Add callback handler for buttons
    application.add_handler(CallbackQueryHandler(button_callback))
    
    logger.info("🤖 Telegram bot initialized successfully!")
    return application

def run_bot(socketio_instance=None):
    """Run the bot"""
    app = init_bot(socketio_instance)
    if app:
        logger.info("🚀 Starting Telegram bot...")
        app.run_polling(allowed_updates=Update.ALL_TYPES)

# ============================================================================

# bot.py - Complete Telegram Bot with Modular Structure
# No updates needed - just copy and paste

# ============================================================================
# BOT INITIALIZATION
# ============================================================================

def init_bot(socketio_instance=None):
    """Initialize the bot with Socket.IO instance"""
    global socketio
    socketio = socketio_instance
    
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not set! Bot will not start.")
        return None
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("login", login_command))
    application.add_handler(CommandHandler("play", play_command))
    application.add_handler(CommandHandler("room", room_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Add callback handler for buttons
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Import and init Socket.IO for play command
    from bot_handlers.play import init_socketio
    init_socketio(socketio)
    
    logger.info("🤖 Telegram bot initialized successfully!")
    return application

def run_bot(socketio_instance=None):
    """Run the bot"""
    app = init_bot(socketio_instance)
    if app:
        logger.info("🚀 Starting Telegram bot...")
        app.run_polling(allowed_updates=["message", "callback_query"])

def start_bot_background(socketio_instance=None):
    """Start the Telegram bot in a background thread"""
    def bot_thread():
        try:
            run_bot(socketio_instance)
        except Exception as e:
            logger.error(f"❌ Bot error: {e}")
    
    thread = threading.Thread(target=bot_thread, daemon=True)
    thread.start()
    logger.info("🤖 Telegram bot thread started in background")
    return thread

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    run_bot()
# MAIN
# ============================================================================

if __name__ == '__main__':
    run_bot()
