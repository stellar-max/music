# bot_handlers/start.py - /start command handler

import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot_config import config, logger
from bot_services.auth_service import create_user, get_user_by_telegram_id, create_auth_token

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
    login_url = f"{config.WEBAPP_URL}/auth/browser/{token}"
    
    keyboard = [
        [InlineKeyboardButton("🎵 Open Web Player", url=login_url)],
        [InlineKeyboardButton("📱 Open in App", url=f"{config.WEBAPP_URL}/app")],
        [InlineKeyboardButton("👥 Create Room", callback_data="create_room")],
        [InlineKeyboardButton("🎧 My Library", callback_data="my_library")],
        [InlineKeyboardButton("📋 List Rooms", callback_data="list_rooms")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = config.WELCOME_TEXT.format(first_name=user.first_name)
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    logger.info(f"User {user.username} ({telegram_id}) started bot")
