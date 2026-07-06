# bot_services/player_service.py - Player control service

import sqlite3
from datetime import datetime
from bot_config import config, logger

def play_track(track_id: int, user_id: int) -> bool:
    """Play a track (increment play count)"""
    conn = sqlite3.connect(config.DB_FILE)
    c = conn.cursor()
    try:
        c.execute(
            "UPDATE tracks SET plays_count = COALESCE(plays_count, 0) + 1 WHERE id = ?",
            (track_id,)
        )
        c.execute(
            """INSERT INTO track_plays (user_id, track_id, play_count, last_played_at)
               VALUES (?, ?, 1, datetime('now'))
               ON CONFLICT(user_id, track_id) DO UPDATE SET
               play_count = play_count + 1,
               last_played_at = datetime('now')""",
            (user_id, track_id)
        )
        conn.commit()
        logger.info(f"Track {track_id} played by user {user_id}")
        return True
    except sqlite3.Error as e:
        logger.error(f"Error playing track: {e}")
        return False
    finally:
        conn.close()

def get_current_track(room_id: str):
    """Get current playing track in a room"""
    conn = sqlite3.connect(config.DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT t.*, r.current_time, r.is_playing
        FROM rooms r
        JOIN tracks t ON r.current_track_id = t.id
        WHERE r.id = ?
    """, (room_id,))
    track = c.fetchone()
    conn.close()
    return dict(track) if track else None

def get_queue(room_id: str):
    """Get queue for a room"""
    conn = sqlite3.connect(config.DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT rq.*, t.title, t.artist, t.filename, u.display_name as added_by_name
        FROM room_queue rq
        JOIN tracks t ON rq.track_id = t.id
        JOIN users u ON rq.added_by_id = u.id
        WHERE rq.room_id = ?
        ORDER BY rq.sort_order ASC, rq.created_at ASC
    """, (room_id,))
    queue = [dict(row) for row in c.fetchall()]
    conn.close()
    return queue
