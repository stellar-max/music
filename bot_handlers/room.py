"""Handles the /room command and displays collaborative room options."""

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


async def room_command(
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
            "➕ Create Room",
            url=mini_app_link("create_room"),
        ),
        InlineKeyboardButton(
            "👥 Active Rooms",
            callback_data="list_rooms",
        ),
        InlineKeyboardButton(
            "🔗 Join Room",
            url=mini_app_link("join_room"),
        ),
        InlineKeyboardButton(
            "🎵 Open Player",
            url=mini_app_link("home"),
        ),
        InlineKeyboardButton(
            "📚 My Library",
            callback_data="my_library",
        ),
        InlineKeyboardButton(
            "🏠 Main Menu",
            callback_data="main_menu",
        ),
    ]

    await message.reply_text(
        f"🎧 <b>{bot_name} Rooms</b>\n\n"
        "Create a collaborative room, join your friends, "
        "or browse active listening rooms.",
        reply_markup=InlineKeyboardMarkup(
            button_rows(
                buttons,
                columns=2,
            )
        ),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )

    if user:
        logger.info(
            "Telegram user %s opened room management",
            user.id,
        )
