# bot_handlers/utils.py - Bot utilities

import re
import sqlite3
from datetime import datetime
from bot_config import config, logger

def validate_song_name(song_name: str) -> bool:
    """Validate song name input"""
    if not song_name or len(song_name) < 1:
        return False
    if len(song_name) > 200:
        return False
    # Check for malicious characters
    if re.search(r'[<>"\'/;]', song_name):
        return False
    return True

def format_track_info(track) -> str:
    """Format track information for display"""
    return f"**{track['title']}** - {track['artist']}"

def get_track_by_id(track_id: int):
    """Get track by ID from database"""
    conn = sqlite3.connect(config.DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM tracks WHERE id = ? AND hidden = 0", (track_id,))
    track = c.fetchone()
    conn.close()
    return dict(track) if track else None

def get_tracks_by_search(query: str, limit: int = 5):
    """Search tracks by title or artist"""
    conn = sqlite3.connect(config.DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(
        """SELECT * FROM tracks 
           WHERE (title LIKE ? OR artist LIKE ?) AND hidden = 0 
           ORDER BY plays_count DESC LIMIT ?""",
        (f"%{query}%", f"%{query}%", limit)
    )
    tracks = c.fetchall()
    conn.close()
    return [dict(track) for track in tracks]

def get_room_info(room_id: str):
    """Get room information by ID"""
    conn = sqlite3.connect(config.DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT r.*, COUNT(rm.id) as member_count, u.display_name as host_name
        FROM rooms r
        JOIN users u ON r.host_id = u.id
        LEFT JOIN room_members rm ON r.id = rm.room_id
        WHERE r.id = ?
        GROUP BY r.id
    """, (room_id,))
    room = c.fetchone()
    conn.close()
    return dict(room) if room else None# bot_handlers/utils.py - Bot utilities

import re
import sqlite3
from datetime import datetime
from bot_config import config, logger

def validate_song_name(song_name: str) -> bool:
    """Validate song name input"""
    if not song_name or len(song_name) < 1:
        return False
    if len(song_name) > 200:
        return False
    # Check for malicious characters
    if re.search(r'[<>"\'/;]', song_name):
        return False
    return True

def format_track_info(track) -> str:
    """Format track information for display"""
    return f"**{track['title']}** - {track['artist']}"

def get_track_by_id(track_id: int):
    """Get track by ID from database"""
    conn = sqlite3.connect(config.DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM tracks WHERE id = ? AND hidden = 0", (track_id,))
    track = c.fetchone()
    conn.close()
    return dict(track) if track else None

def get_tracks_by_search(query: str, limit: int = 5):
    """Search tracks by title or artist"""
    conn = sqlite3.connect(config.DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(
        """SELECT * FROM tracks 
           WHERE (title LIKE ? OR artist LIKE ?) AND hidden = 0 
           ORDER BY plays_count DESC LIMIT ?""",
        (f"%{query}%", f"%{query}%", limit)
    )
    tracks = c.fetchall()
    conn.close()
    return [dict(track) for track in tracks]

def get_room_info(room_id: str):
    """Get room information by ID"""
    conn = sqlite3.connect(config.DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT r.*, COUNT(rm.id) as member_count, u.display_name as host_name
        FROM rooms r
        JOIN users u ON r.host_id = u.id
        LEFT JOIN room_members rm ON r.id = rm.room_id
        WHERE r.id = ?
        GROUP BY r.id
    """, (room_id,))
    room = c.fetchone()
    conn.close()
    return dict(room) if room else None
