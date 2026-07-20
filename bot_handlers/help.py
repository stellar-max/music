"""Handles the /help command."""

from html import escape

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes

from bot_config import config, logger
from bot_handlers.utils import (
    button_rows,
    mini_app_link,
)


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    message = update.effective_message
    user = update.effective_user

    if not message:
        return

    bot_name = escape(
        getattr(
            config,
            "BOT_NAME",
            "Music Player",
        )
    )

    buttons = [
        InlineKeyboardButton(
            "🎵 Open Player",
            url=mini_app_link("home"),
        ),
        InlineKeyboardButton(
            "🎧 Create Room",
            url=mini_app_link("create_room"),
        ),
        InlineKeyboardButton(
            "👥 Active Rooms",
            callback_data="list_rooms",
        ),
        InlineKeyboardButton(
            "📚 My Library",
            callback_data="my_library",
        ),
    ]

    await message.reply_text(
        f"ℹ️ <b>{bot_name} Help</b>\n\n"
        "<b>Commands</b>\n"
        "• /start — Main menu\n"
        "• /login — Secure login\n"
        "• /play &lt;song&gt; — Search tracks\n"
        "• /room — Manage rooms\n"
        "• /help — Show help",
        reply_markup=InlineKeyboardMarkup(
            button_rows(buttons, columns=2)
        ),
        parse_mode="HTML",
    )

    if user:
        logger.info(
            "Telegram user %s requested help",
            user.id,
        )
