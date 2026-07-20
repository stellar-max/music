"""Handles track searches and broadcasts playback requests through Socket.IO."""

from datetime import datetime, timezone
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
    get_tracks_by_search,
    mini_app_link,
    validate_song_name,
)


socketio = None


def init_socketio(socketio_instance) -> None:
    global socketio
    socketio = socketio_instance


async def play_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    if not context.args:
        await message.reply_text(
            "🎵 <b>Usage</b>\n\n"
            "<code>/play song name</code>\n\n"
            "Example: <code>/play Bohemian Rhapsody</code>",
            parse_mode="HTML",
        )
        return

    song_name = " ".join(context.args).strip()

    if not validate_song_name(song_name):
        await message.reply_text(
            "Enter a valid song or artist name."
        )
        return

    results = get_tracks_by_search(
        song_name,
        limit=5,
    )

    if socketio is not None:
        try:
            socketio.emit(
                "telegram_play",
                {
                    "song": song_name,
                    "user": (
                        user.username
                        or user.first_name
                        or str(user.id)
                    ),
                    "user_id": user.id,
                    "timestamp": datetime.now(
                        timezone.utc
                    ).isoformat(),
                },
            )

            logger.info(
                "Broadcast play request %s from Telegram user %s",
                song_name,
                user.id,
            )

        except Exception:
            logger.exception(
                "Failed to emit Telegram playback request"
            )

    buttons = []

    if results:
        lines = [
            f"🎵 <b>Results for “{escape(song_name)}”</b>",
            "",
        ]

        for track in results:
            title = escape(
                str(track.get("title") or "Unknown title")
            )
            artist = escape(
                str(track.get("artist") or "Unknown artist")
            )

            lines.append(
                f"• <b>{title}</b> — {artist}"
            )

            buttons.append(
                InlineKeyboardButton(
                    f"▶️ {track.get('title', 'Track')[:18]}",
                    url=mini_app_link(
                        f"track_{track['id']}"
                    ),
                )
            )

        reply = "\n".join(lines)

    else:
        reply = (
            f"🎵 <b>No local result for “{escape(song_name)}”</b>\n\n"
            "Open the player to browse your library."
        )

    buttons.extend(
        [
            InlineKeyboardButton(
                "🎵 Open Player",
                url=mini_app_link("home"),
            ),
            InlineKeyboardButton(
                "📚 My Library",
                callback_data="my_library",
            ),
        ]
    )

    await message.reply_text(
        reply,
        reply_markup=InlineKeyboardMarkup(
            button_rows(buttons, columns=2)
        ),
        parse_mode="HTML",
        disable_web_page_preview=True,
                    )
