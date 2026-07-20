"""Manages collaborative rooms, membership, and room queues."""

import sqlite3
import uuid
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


def get_rooms() -> list[dict]:
    connection = _connect()

    try:
        rooms = connection.execute(
            """
            SELECT
                r.*,
                COUNT(DISTINCT rm.user_id) AS member_count,
                u.display_name AS host_name,
                u.nickname AS host_nickname
            FROM rooms AS r
            JOIN users AS u
                ON u.id = r.host_id
            LEFT JOIN room_members AS rm
                ON rm.room_id = r.id
            GROUP BY r.id
            ORDER BY r.created_at DESC
            """
        ).fetchall()

        return [dict(room) for room in rooms]

    except sqlite3.Error:
        logger.exception("Failed to retrieve rooms")
        return []

    finally:
        connection.close()


def create_room(
    name: str,
    host_id: int,
) -> Optional[str]:
    name = str(name or "").strip()

    if not name:
        logger.warning("Room creation rejected: empty name")
        return None

    room_id = uuid.uuid4().hex[:8]
    connection = _connect()

    try:
        host_exists = connection.execute(
            """
            SELECT 1
            FROM users
            WHERE id = ?
            LIMIT 1
            """,
            (host_id,),
        ).fetchone()

        if host_exists is None:
            logger.warning(
                "Room creation rejected: host %s not found",
                host_id,
            )
            return None

        connection.execute("BEGIN IMMEDIATE")

        connection.execute(
            """
            INSERT INTO rooms (
                id,
                name,
                host_id
            )
            VALUES (?, ?, ?)
            """,
            (
                room_id,
                name,
                host_id,
            ),
        )

        connection.execute(
            """
            INSERT INTO room_members (
                room_id,
                user_id
            )
            VALUES (?, ?)
            """,
            (
                room_id,
                host_id,
            ),
        )

        connection.commit()

        logger.info(
            "Created room %s (%s) for host %s",
            name,
            room_id,
            host_id,
        )

        return room_id

    except sqlite3.Error:
        connection.rollback()
        logger.exception(
            "Failed to create room for host %s",
            host_id,
        )
        return None

    finally:
        connection.close()


def join_room(
    room_id: str,
    user_id: int,
) -> bool:
    connection = _connect()

    try:
        room_exists = connection.execute(
            """
            SELECT 1
            FROM rooms
            WHERE id = ?
            LIMIT 1
            """,
            (room_id,),
        ).fetchone()

        if room_exists is None:
            logger.warning(
                "Cannot join missing room %s",
                room_id,
            )
            return False

        user_exists = connection.execute(
            """
            SELECT 1
            FROM users
            WHERE id = ?
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()

        if user_exists is None:
            logger.warning(
                "Cannot add missing user %s to room %s",
                user_id,
                room_id,
            )
            return False

        connection.execute(
            """
            INSERT OR IGNORE INTO room_members (
                room_id,
                user_id
            )
            VALUES (?, ?)
            """,
            (
                room_id,
                user_id,
            ),
        )

        connection.commit()

        logger.info(
            "User %s joined room %s",
            user_id,
            room_id,
        )

        return True

    except sqlite3.Error:
        connection.rollback()
        logger.exception(
            "Failed to join user %s to room %s",
            user_id,
            room_id,
        )
        return False

    finally:
        connection.close()


def leave_room(
    room_id: str,
    user_id: int,
) -> bool:
    connection = _connect()

    try:
        room = connection.execute(
            """
            SELECT host_id
            FROM rooms
            WHERE id = ?
            LIMIT 1
            """,
            (room_id,),
        ).fetchone()

        if room is None:
            return False

        if room["host_id"] == user_id:
            logger.warning(
                "Room host %s cannot leave room %s",
                user_id,
                room_id,
            )
            return False

        cursor = connection.execute(
            """
            DELETE FROM room_members
            WHERE room_id = ?
              AND user_id = ?
            """,
            (
                room_id,
                user_id,
            ),
        )

        connection.commit()

        if cursor.rowcount > 0:
            logger.info(
                "User %s left room %s",
                user_id,
                room_id,
            )
            return True

        return False

    except sqlite3.Error:
        connection.rollback()
        logger.exception(
            "Failed to remove user %s from room %s",
            user_id,
            room_id,
        )
        return False

    finally:
        connection.close()


def add_to_queue(
    room_id: str,
    track_id: int,
    user_id: int,
) -> bool:
    connection = _connect()

    try:
        membership = connection.execute(
            """
            SELECT 1
            FROM room_members
            WHERE room_id = ?
              AND user_id = ?
            LIMIT 1
            """,
            (
                room_id,
                user_id,
            ),
        ).fetchone()

        if membership is None:
            logger.warning(
                "User %s is not a member of room %s",
                user_id,
                room_id,
            )
            return False

        track_exists = connection.execute(
            """
            SELECT 1
            FROM tracks
            WHERE id = ?
              AND hidden = 0
            LIMIT 1
            """,
            (track_id,),
        ).fetchone()

        if track_exists is None:
            logger.warning(
                "Track %s does not exist or is hidden",
                track_id,
            )
            return False

        connection.execute("BEGIN IMMEDIATE")

        maximum_order = connection.execute(
            """
            SELECT COALESCE(MAX(sort_order), 0)
            FROM room_queue
            WHERE room_id = ?
            """,
            (room_id,),
        ).fetchone()[0]

        connection.execute(
            """
            INSERT INTO room_queue (
                room_id,
                track_id,
                added_by_id,
                sort_order
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                room_id,
                track_id,
                user_id,
                maximum_order + 1,
            ),
        )

        connection.commit()

        logger.info(
            "Track %s added to room %s queue by user %s",
            track_id,
            room_id,
            user_id,
        )

        return True

    except sqlite3.Error:
        connection.rollback()
        logger.exception(
            "Failed to add track %s to room %s",
            track_id,
            room_id,
        )
        return False

    finally:
        connection.close()
