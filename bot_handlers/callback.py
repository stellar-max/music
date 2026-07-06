# bot_handlers/callback.py - Button callback handlers

import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot_config import config, logger

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline keyboard button presses"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user = query.from_user
    
    if data == "create_room":
        # Generate room creation link
        room_url = f"{config.WEBAPP_URL}/rooms"
        keyboard = [[InlineKeyboardButton("🎧 Open Room", url=room_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🎧 **Create a Room**\n\n"
            "Click below to open the web player and create a collaborative room.\n\n"
            "Share the room link with friends to listen together!\n\n"
            "🔗 **Room Link:** {room_url}".format(room_url=room_url),
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif data == "list_rooms":
        # Get active rooms
        conn = sqlite3.connect(config.DB_FILE)
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
                reply += f"  Link: {config.WEBAPP_URL}/room/{room['id']}\n\n"
            reply += "\n💡 Click a link above to join a room!"
        else:
            reply = "📋 **No active rooms**\n\nBe the first to create one!\n\n➕ Click 'Create Room' above."
        
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh", callback_data="list_rooms")],
            [InlineKeyboardButton("➕ Create Room", callback_data="create_room")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            reply,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif data == "join_room":
        await query.edit_message_text(
            f"🔗 **Join a Room**\n\n"
            f"1. Open the web player: {config.WEBAPP_URL}\n"
            f"2. Go to 'Rooms'\n"
            f"3. Click 'Join Room' and enter the room ID\n\n"
            f"Or use a direct link:\n"
            f"{config.WEBAPP_URL}/room/<room_id>",
            parse_mode='Markdown'
        )
    
    elif data == "my_library":
        # Get user library link
        conn = sqlite3.connect(config.DB_FILE)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT nickname FROM users WHERE telegram_id = ?", (user.id,))
        user_db = c.fetchone()
        conn.close()
        
        if user_db:
            library_url = f"{config.WEBAPP_URL}/user/{user_db['nickname']}"
            keyboard = [[InlineKeyboardButton("📚 Open Library", url=library_url)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "📚 **Your Library**\n\n"
                "Click below to view your uploaded tracks and albums!\n\n"
                f"🔗 **Link:** {library_url}",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                "❌ **User not found**\n\n"
                "Please use /start first to register.",
                parse_mode='Markdown'
            )
    
    elif data == "refresh_rooms":
        await query.edit_message_text(
            "🔄 **Refreshing...**\n\n"
            "Click below to see the latest rooms.",
            parse_mode='Markdown'
        )
        # Re-trigger list_rooms
        await button_callback(update, context)
    
    logger.info(f"User {user.username} pressed button: {data}")
