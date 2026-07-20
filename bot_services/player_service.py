"""Manages track playback counts and room playback information."""

import sqlite3
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


def play_track(
    track_id: int,
    user_id: int,
) -> bool:
    connection = _connect()

    try:
        connection.execute("BEGIN IMMEDIATE")

        track_cursor = connection.execute(
            """
            UPDATE tracks
            SET plays_count = COALESCE(plays_count, 0) + 1
            WHERE id = ?
              AND hidden = 0
            """,
            (track_id,),
        )

        if track_cursor.rowcount == 0:
            connection.rollback()

            logger.warning(
                "Cannot play missing or hidden track %s",
                track_id,
            )
            return False

        connection.execute(
            """
            INSERT INTO track_plays (
                user_id,
                track_id,
                play_count,
                last_played_at
            )
            VALUES (?, ?, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, track_id)
            DO UPDATE SET
                play_count = track_plays.play_count + 1,
                last_played_at = CURRENT_TIMESTAMP
            """,
            (
                user_id,
                track_id,
            ),
        )

        connection.commit()

        logger.info(
            "Track %s played by user %s",
            track_id,
            user_id,
        )

        return True

    except sqlite3.Error:
        connection.rollback()
        logger.exception(
            "Failed to play track %s for user %s",
            track_id,
            user_id,
        )
        return False

    finally:
        connection.close()


def get_current_track(
    room_id: str,
) -> Optional[dict]:
    connection = _connect()

    try:
        track = connection.execute(
            """
            SELECT
                t.*,
                r.current_time,
                r.is_playing,
                r.id AS room_id,
                r.name AS room_name
            FROM rooms AS r
            JOIN tracks AS t
                ON t.id = r.current_track_id
            WHERE r.id = ?
            LIMIT 1
            """,
            (room_id,),
        ).fetchone()

        return dict(track) if track else None

    except sqlite3.Error:
        logger.exception(
            "Failed to get current track for room %s",
            room_id,
        )
        return None

    finally:
        connection.close()


def get_queue(
    room_id: str,
) -> list[dict]:
    connection = _connect()

    try:
        queue = connection.execute(
            """
            SELECT
                rq.id AS queue_id,
                rq.room_id,
                rq.track_id,
                rq.added_by_id,
                rq.sort_order,
                rq.created_at,
                t.title,
                t.artist,
                t.filename,
                t.cover_filename,
                COALESCE(
                    u.display_name,
                    u.nickname,
                    u.username,
                    'Unknown'
                ) AS added_by_name
            FROM room_queue AS rq
            JOIN tracks AS t
                ON t.id = rq.track_id
            LEFT JOIN users AS u
                ON u.id = rq.added_by_id
            WHERE rq.room_id = ?
            ORDER BY
                rq.sort_order ASC,
                rq.created_at ASC,
                rq.id ASC
            """,
            (room_id,),
        ).fetchall()

        return [dict(item) for item in queue]

    except sqlite3.Error:
        logger.exception(
            "Failed to retrieve queue for room %s",
            room_id,
        )
        return []

    finally:
        connection.close()
