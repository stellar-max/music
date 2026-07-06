# bot_services/room_service.py - Room management service

import sqlite3
import uuid
from datetime import datetime
from bot_config import config, logger

def get_rooms():
    """Get all active rooms"""
    conn = sqlite3.connect(config.DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT r.*, COUNT(rm.id) as member_count, u.display_name as host_name
        FROM rooms r
        JOIN users u ON r.host_id = u.id
        LEFT JOIN room_members rm ON r.id = rm.room_id
        GROUP BY r.id
        ORDER BY r.created_at DESC
    """)
    rooms = [dict(row) for row in c.fetchall()]
    conn.close()
    return rooms

def create_room(name: str, host_id: int) -> str:
    """Create a new collaborative room"""
    room_id = str(uuid.uuid4())[:8]
    
    conn = sqlite3.connect(config.DB_FILE)
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO rooms (id, name, host_id) VALUES (?, ?, ?)",
            (room_id, name, host_id)
        )
        c.execute(
            "INSERT INTO room_members (room_id, user_id) VALUES (?, ?)",
            (room_id, host_id)
        )
        conn.commit()
        logger.info(f"Created room: {name} ({room_id}) by host {host_id}")
        return room_id
    except sqlite3.IntegrityError as e:
        logger.error(f"Error creating room: {e}")
        return None
    finally:
        conn.close()

def join_room(room_id: str, user_id: int) -> bool:
    """Add a user to a room"""
    conn = sqlite3.connect(config.DB_FILE)
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO room_members (room_id, user_id) VALUES (?, ?)",
            (room_id, user_id)
        )
        conn.commit()
        logger.info(f"User {user_id} joined room {room_id}")
        return True
    except sqlite3.IntegrityError:
        logger.warning(f"User {user_id} already in room {room_id}")
        return False
    finally:
        conn.close()

def leave_room(room_id: str, user_id: int) -> bool:
    """Remove a user from a room"""
    conn = sqlite3.connect(config.DB_FILE)
    c = conn.cursor()
    c.execute(
        "DELETE FROM room_members WHERE room_id = ? AND user_id = ?",
        (room_id, user_id)
    )
    conn.commit()
    deleted = c.rowcount > 0
    conn.close()
    if deleted:
        logger.info(f"User {user_id} left room {room_id}")
    return deleted

def add_to_queue(room_id: str, track_id: int, user_id: int) -> bool:
    """Add a track to room queue"""
    conn = sqlite3.connect(config.DB_FILE)
    c = conn.cursor()
    try:
        # Get max sort order
        c.execute("SELECT MAX(sort_order) FROM room_queue WHERE room_id = ?", (room_id,))
        max_order = c.fetchone()[0] or 0
        
        c.execute(
            "INSERT INTO room_queue (room_id, track_id, added_by_id, sort_order) VALUES (?, ?, ?, ?)",
            (room_id, track_id, user_id, max_order + 1)
        )
        conn.commit()
        logger.info(f"Track {track_id} added to queue in room {room_id}")
        return True
    except sqlite3.IntegrityError as e:
        logger.error(f"Error adding to queue: {e}")
        return False
    finally:
        conn.close()
