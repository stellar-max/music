"""Handles secure browser-login link generation."""

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes

from bot_config import logger
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


async def login_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    user = update.effective_user
    message = update.effective_message

    if not user or not message:
        return

    existing_user = get_user_by_telegram_id(user.id)

    if not existing_user:
        created_user = create_user(
            telegram_id=user.id,
            username=user.username or "",
            first_name=user.first_name or "",
            last_name=user.last_name or "",
        )

        if not created_user:
            await message.reply_text(
                "Unable to create your account. Please try again."
            )
            return

    token = create_auth_token(user.id)

    if not token:
        await message.reply_text(
            "Unable to generate your login link. Please try again."
        )
        return

    buttons = [
        InlineKeyboardButton(
            "🔐 Secure Login",
            url=build_login_url(token),
        ),
        InlineKeyboardButton(
            "🎵 Open Player",
            url=mini_app_link("home"),
        ),
    ]

    await message.reply_text(
        "🔐 <b>Your secure login is ready</b>\n\n"
        "The login link expires in 10 minutes.",
        reply_markup=InlineKeyboardMarkup(
            button_rows(buttons, columns=2)
        ),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )

    logger.info(
        "Telegram user %s generated a login token",
        user.id,
    )
