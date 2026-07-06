# bot_handlers/login.py - /login command handler

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot_config import config, logger
from bot_services.auth_service import create_auth_token

async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /login - Generate a new login link"""
    user = update.effective_user
    token = create_auth_token(user.id)
    login_url = f"{config.WEBAPP_URL}/auth/browser/{token}"
    
    keyboard = [[InlineKeyboardButton("🔑 Login to Web Player", url=login_url)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🔑 **Your login link is ready!**\n\n"
        f"Click the button below to log in to the web player.\n\n"
        f"⏰ This link expires in 10 minutes.\n\n"
        f"🌐 **Web Player:** {config.WEBAPP_URL}",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    logger.info(f"User {user.username} generated login link")
