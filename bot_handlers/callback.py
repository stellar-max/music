"""Handles inline menu actions and Telegram Mini App deep links."""

import sqlite3
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


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(
        config.DB_FILE,
        timeout=30,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout = 30000")
    return connection


async def show_rooms(query) -> None:
    connection = get_connection()

    try:
        rooms = connection.execute(
            """
            SELECT
                r.id,
                r.name,
                r.created_at,
                COUNT(DISTINCT rm.user_id) AS member_count,
                COALESCE(
                    u.display_name,
                    u.nickname,
                    u.username,
                    'Unknown'
                ) AS host_name
            FROM rooms AS r
            JOIN users AS u
                ON u.id = r.host_id
            LEFT JOIN room_members AS rm
                ON rm.room_id = r.id
            GROUP BY r.id
            ORDER BY r.created_at DESC
            LIMIT 6
            """
        ).fetchall()

    except sqlite3.Error:
        logger.exception("Failed to load active rooms")

        await query.edit_message_text(
            "Unable to load rooms right now. Please try again."
        )
        return

    finally:
        connection.close()

    buttons = []

    if rooms:
        lines = [
            "👥 <b>Active Rooms</b>",
            "",
        ]

        for room in rooms:
            room_name = escape(
                str(room["name"] or "Unnamed Room")
            )
            host_name = escape(
                str(room["host_name"] or "Unknown")
            )

            lines.append(
                f"• <b>{room_name}</b>\n"
                f"  {room['member_count']} members · Host: {host_name}"
            )

            buttons.append(
                InlineKeyboardButton(
                    f"🎧 {room['name'][:18]}",
                    url=mini_app_link(
                        f"room_{room['id']}"
                    ),
                )
            )

        text = "\n\n".join(lines)

    else:
        text = (
            "👥 <b>No Active Rooms</b>\n\n"
            "Create a room and invite friends to listen together."
        )

    buttons.extend(
        [
            InlineKeyboardButton(
                "➕ Create Room",
                url=mini_app_link("create_room"),
            ),
            InlineKeyboardButton(
                "🔄 Refresh",
                callback_data="list_rooms",
            ),
            InlineKeyboardButton(
                "🏠 Main Menu",
                callback_data="main_menu",
            ),
        ]
    )

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            button_rows(buttons, columns=2)
        ),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


async def button_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query

    if not query:
        return

    await query.answer()

    data = query.data or ""
    user = query.from_user

    if data == "create_room":
        buttons = [
            InlineKeyboardButton(
                "🎧 Open Mini App",
                url=mini_app_link("create_room"),
            ),
            InlineKeyboardButton(
                "👥 Active Rooms",
                callback_data="list_rooms",
            ),
            InlineKeyboardButton(
                "🏠 Main Menu",
                callback_data="main_menu",
            ),
        ]

        await query.edit_message_text(
            "🎧 <b>Create a Room</b>\n\n"
            "Open the Telegram Mini App to create a collaborative "
            "listening room and share it with friends.",
            reply_markup=InlineKeyboardMarkup(
                button_rows(buttons, columns=2)
            ),
            parse_mode="HTML",
        )

    elif data == "list_rooms":
        await show_rooms(query)

    elif data == "my_library":
        connection = get_connection()

        try:
            user_row = connection.execute(
                """
                SELECT nickname
                FROM users
                WHERE telegram_id = ?
                LIMIT 1
                """,
                (user.id,),
            ).fetchone()

        except sqlite3.Error:
            logger.exception(
                "Failed to retrieve library for Telegram user %s",
                user.id,
            )
            user_row = None

        finally:
            connection.close()

        if not user_row:
            await query.edit_message_text(
                "Account not found. Send /start to register first.",
                parse_mode="HTML",
            )
            return

        nickname = str(user_row["nickname"])

        buttons = [
            InlineKeyboardButton(
                "📚 Open Library",
                url=mini_app_link(
                    f"library_{nickname}"
                ),
            ),
            InlineKeyboardButton(
                "🎵 Open Player",
                url=mini_app_link("home"),
            ),
            InlineKeyboardButton(
                "🏠 Main Menu",
                callback_data="main_menu",
            ),
        ]

        await query.edit_message_text(
            "📚 <b>Your Library</b>\n\n"
            "Open the Mini App to view your tracks and albums.",
            reply_markup=InlineKeyboardMarkup(
                button_rows(buttons, columns=2)
            ),
            parse_mode="HTML",
        )

    elif data == "show_help":
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
                "👥 Active Rooms",
                callback_data="list_rooms",
            ),
            InlineKeyboardButton(
                "🏠 Main Menu",
                callback_data="main_menu",
            ),
        ]

        await query.edit_message_text(
            f"ℹ️ <b>{bot_name} Help</b>\n\n"
            "<b>Commands</b>\n"
            "• /start — Open the main menu\n"
            "• /login — Generate a secure login\n"
            "• /play &lt;song&gt; — Search a track\n"
            "• /room — Manage rooms\n"
            "• /help — Show help",
            reply_markup=InlineKeyboardMarkup(
                button_rows(buttons, columns=2)
            ),
            parse_mode="HTML",
        )

    elif data == "main_menu":
        buttons = [
            InlineKeyboardButton(
                "🎵 Open Player",
                url=mini_app_link("home"),
            ),
            InlineKeyboardButton(
                "🔐 Secure Login",
                callback_data="secure_login",
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

        await query.edit_message_text(
            f"🎵 <b>{escape(config.BOT_NAME)}</b>\n\n"
            "Choose an option below.",
            reply_markup=InlineKeyboardMarkup(
                button_rows(buttons, columns=2)
            ),
            parse_mode="HTML",
        )

    elif data == "secure_login":
        await query.edit_message_text(
            "Send /login to generate a fresh secure login link.",
            parse_mode="HTML",
        )

    logger.info(
        "Telegram user %s pressed callback %s",
        user.id,
        data,
    )
