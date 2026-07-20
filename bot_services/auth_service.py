"""Manages Telegram users and temporary web authentication tokens."""

import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Optional

from bot_config import config, logger


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(
        config.DB_FILE,
        timeout=30,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 30000")
    return connection


def _get_unique_nickname(
    connection: sqlite3.Connection,
    preferred: str,
    telegram_id: int,
) -> str:
    base_nickname = preferred.strip().lstrip("@")

    if not base_nickname:
        base_nickname = f"user_{telegram_id}"

    existing = connection.execute(
        """
        SELECT telegram_id
        FROM users
        WHERE nickname = ?
        LIMIT 1
        """,
        (base_nickname,),
    ).fetchone()

    if existing is None or existing["telegram_id"] == telegram_id:
        return base_nickname

    return f"{base_nickname}_{telegram_id}"


def create_user(
    telegram_id: int,
    username: str = "",
    first_name: str = "",
    last_name: str = "",
) -> Optional[int]:
    username = username or ""
    first_name = first_name or ""
    last_name = last_name or ""

    display_name = " ".join(
        part.strip()
        for part in (first_name, last_name)
        if part and part.strip()
    )

    if not display_name:
        display_name = username or f"User {telegram_id}"

    connection = _connect()

    try:
        existing = connection.execute(
            """
            SELECT id, nickname
            FROM users
            WHERE telegram_id = ?
            LIMIT 1
            """,
            (telegram_id,),
        ).fetchone()

        if existing:
            connection.execute(
                """
                UPDATE users
                SET username = ?,
                    first_name = ?,
                    last_name = ?,
                    display_name = ?
                WHERE telegram_id = ?
                """,
                (
                    username,
                    first_name,
                    last_name,
                    display_name,
                    telegram_id,
                ),
            )

            connection.commit()

            logger.info(
                "Updated Telegram user %s",
                telegram_id,
            )
            return existing["id"]

        nickname = _get_unique_nickname(
            connection,
            username,
            telegram_id,
        )

        cursor = connection.execute(
            """
            INSERT INTO users (
                telegram_id,
                username,
                first_name,
                last_name,
                display_name,
                nickname
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                telegram_id,
                username,
                first_name,
                last_name,
                display_name,
                nickname,
            ),
        )

        connection.commit()

        logger.info(
            "Created Telegram user %s with database ID %s",
            telegram_id,
            cursor.lastrowid,
        )

        return cursor.lastrowid

    except sqlite3.Error:
        connection.rollback()
        logger.exception(
            "Failed to create or update Telegram user %s",
            telegram_id,
        )
        return None

    finally:
        connection.close()


def get_user_by_telegram_id(
    telegram_id: int,
) -> Optional[dict]:
    connection = _connect()

    try:
        user = connection.execute(
            """
            SELECT *
            FROM users
            WHERE telegram_id = ?
            LIMIT 1
            """,
            (telegram_id,),
        ).fetchone()

        return dict(user) if user else None

    except sqlite3.Error:
        logger.exception(
            "Failed to retrieve Telegram user %s",
            telegram_id,
        )
        return None

    finally:
        connection.close()


def create_auth_token(
    telegram_id: int,
) -> Optional[str]:
    token = secrets.token_hex(16)

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(minutes=10)
    ).strftime("%Y-%m-%d %H:%M:%S")

    connection = _connect()

    try:
        user_exists = connection.execute(
            """
            SELECT 1
            FROM users
            WHERE telegram_id = ?
            LIMIT 1
            """,
            (telegram_id,),
        ).fetchone()

        if user_exists is None:
            logger.error(
                "Cannot create token: Telegram user %s does not exist",
                telegram_id,
            )
            return None

        connection.execute(
            """
            DELETE FROM auth_tokens
            WHERE expires_at <= CURRENT_TIMESTAMP
            """
        )

        connection.execute(
            """
            INSERT INTO auth_tokens (
                token,
                telegram_id,
                expires_at
            )
            VALUES (?, ?, ?)
            """,
            (
                token,
                telegram_id,
                expires_at,
            ),
        )

        connection.commit()

        logger.info(
            "Created authentication token for Telegram user %s",
            telegram_id,
        )

        return token

    except sqlite3.Error:
        connection.rollback()
        logger.exception(
            "Failed to create authentication token for %s",
            telegram_id,
        )
        return None

    finally:
        connection.close()


def verify_auth_token(
    token: str,
) -> Optional[dict]:
    if not token:
        return None

    connection = _connect()

    try:
        result = connection.execute(
            """
            SELECT
                token,
                telegram_id,
                created_at,
                expires_at
            FROM auth_tokens
            WHERE token = ?
              AND expires_at > CURRENT_TIMESTAMP
            LIMIT 1
            """,
            (token,),
        ).fetchone()

        return dict(result) if result else None

    except sqlite3.Error:
        logger.exception(
            "Failed to verify authentication token"
        )
        return None

    finally:
        connection.close()
