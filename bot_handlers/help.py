# bot_handlers/help.py - /help command handler

from telegram import Update
from telegram.ext import ContextTypes
from bot_config import config, logger

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help - Show help message"""
    help_text = config.HELP_TEXT.format(WEBAPP_URL=config.WEBAPP_URL)
    
    await update.message.reply_text(
        help_text,
        parse_mode='Markdown'
    )
    
    logger.info(f"User {update.effective_user.username} requested help")
