"""Handles /start and displays the primary Telegram Mini App menu."""

from html import escape

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes

from bot_config import config, logger
from bot_handlers.utils import (
    build_login_url,
    button_rows,
    mini_app_link,
)
from bot_services.auth_service import (
    create_auth_token,
    create_user,
    get_user_by_telegram_id,
)


async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    user = update.effective_user
    message = update.effective_message

    if not user or not message:
        return

    telegram_id = user.id
    username = user.username or ""
    first_name = user.first_name or "there"
    last_name = user.last_name or ""

    existing_user = get_user_by_telegram_id(
        telegram_id
    )

    if not existing_user:
        user_id = create_user(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )

        if not user_id:
            await message.reply_text(
                "Unable to create your account. Please try again."
            )
            return

    token = create_auth_token(telegram_id)

    if not token:
        await message.reply_text(
            "Unable to generate your login link. Please try again."
        )
        return

    login_url = build_login_url(token)

    buttons = [
        InlineKeyboardButton(
            "🎵 Open Player",
            url=mini_app_link("home"),
        ),
        InlineKeyboardButton(
            "🔐 Secure Login",
            url=login_url,
        ),
        InlineKeyboardButton(
            "🎧 Create Room",
            callback_data="create_room",
        ),
        InlineKeyboardButton(
            "📚 My Library",
            callback_data="my_library",
        ),
        InlineKeyboardButton(
            "👥 Active Rooms",
            callback_data="list_rooms",
        ),
        InlineKeyboardButton(
            "ℹ️ Help",
            callback_data="show_help",
        ),
    ]

    bot_name = escape(
        getattr(
            config,
            "BOT_NAME",
            "Music Player",
        )
    )

    safe_first_name = escape(first_name)

    welcome_text = (
        f"🎵 <b>Welcome to {bot_name}, {safe_first_name}!</b>\n\n"
        "Stream your music, manage your library and listen "
        "together through collaborative rooms.\n\n"
        "Choose an option below to continue."
    )

    await message.reply_text(
        welcome_text,
        reply_markup=InlineKeyboardMarkup(
            button_rows(buttons, columns=2)
        ),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )

    logger.info(
        "User %s (@%s) started the bot",
        telegram_id,
        username or "none",
    )
