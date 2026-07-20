"""Provides shared validation, formatting, database, and Mini App link helpers."""

import re
import sqlite3
from html import escape
from typing import Optional

from telegram import InlineKeyboardButton

from bot_config import config, logger


def get_db_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(
        config.DB_FILE,
        timeout=30,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 30000")
    return connection


def button_rows(
    buttons: list[InlineKeyboardButton],
    columns: int = 2,
) -> list[list[InlineKeyboardButton]]:
    columns = max(1, columns)

    return [
        buttons[index:index + columns]
        for index in range(0, len(buttons), columns)
    ]


def clean_start_param(value: str) -> str:
    value = re.sub(
        r"[^A-Za-z0-9_-]",
        "_",
        str(value or ""),
    )

    value = value.strip("_")[:64]
    return value or "home"


def mini_app_link(start_param: str = "home") -> str:
    start_param = clean_start_param(start_param)

    link_builder = getattr(
        config,
        "mini_app_deep_link",
        None,
    )

    if callable(link_builder):
        return link_builder(start_param)

    bot_username = getattr(
        config,
        "BOT_USERNAME",
        "",
    ).lstrip("@")

    if bot_username:
        return (
            f"https://t.me/{bot_username}"
            f"?startapp={start_param}"
        )

    return config.WEBAPP_URL.rstrip("/")


def build_login_url(token: str) -> str:
    base_url = config.WEBAPP_URL.rstrip("/")

    login_path = getattr(
        config,
        "LOGIN_PATH",
        "/auth/browser",
    )

    login_path = f"/{login_path.strip('/')}"

    return f"{base_url}{login_path}/{token}"


def validate_song_name(song_name: str) -> bool:
    song_name = str(song_name or "").strip()

    if not song_name or len(song_name) > 200:
        return False

    return not any(
        ord(character) < 32
        and character not in "\n\r\t"
        for character in song_name
    )


def format_track_info(track: dict) -> str:
    title = escape(
        str(track.get("title") or "Unknown title")
    )
    artist = escape(
        str(track.get("artist") or "Unknown artist")
    )

    return f"<b>{title}</b> — {artist}"


def get_track_by_id(
    track_id: int,
) -> Optional[dict]:
    connection = get_db_connection()

    try:
        track = connection.execute(
            """
            SELECT *
            FROM tracks
            WHERE id = ?
              AND hidden = 0
            LIMIT 1
            """,
            (track_id,),
        ).fetchone()

        return dict(track) if track else None

    except sqlite3.Error:
        logger.exception(
            "Failed to retrieve track %s",
            track_id,
        )
        return None

    finally:
        connection.close()


def get_tracks_by_search(
    query: str,
    limit: int = 5,
) -> list[dict]:
    query = str(query or "").strip()

    if not query:
        return []

    limit = max(1, min(int(limit), 10))
    search_term = f"%{query}%"

    connection = get_db_connection()

    try:
        tracks = connection.execute(
            """
            SELECT *
            FROM tracks
            WHERE (
                title LIKE ?
                OR artist LIKE ?
            )
              AND hidden = 0
            ORDER BY
                COALESCE(plays_count, 0) DESC,
                created_at DESC
            LIMIT ?
            """,
            (
                search_term,
                search_term,
                limit,
            ),
        ).fetchall()

        return [dict(track) for track in tracks]

    except sqlite3.Error:
        logger.exception(
            "Failed to search tracks for %s",
            query,
        )
        return []

    finally:
        connection.close()


def get_room_info(
    room_id: str,
) -> Optional[dict]:
    connection = get_db_connection()

    try:
        room = connection.execute(
            """
            SELECT
                r.*,
                COUNT(DISTINCT rm.user_id) AS member_count,
                u.display_name AS host_name
            FROM rooms AS r
            JOIN users AS u
                ON u.id = r.host_id
            LEFT JOIN room_members AS rm
                ON rm.room_id = r.id
            WHERE r.id = ?
            GROUP BY r.id
            LIMIT 1
            """,
            (room_id,),
        ).fetchone()

        return dict(room) if room else None

    except sqlite3.Error:
        logger.exception(
            "Failed to retrieve room %s",
            room_id,
        )
        return None

    finally:
        connection.close()
