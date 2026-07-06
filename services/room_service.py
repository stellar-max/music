# services/room_service.py
# Room service for collaborative listening features

import sqlite3
from typing import Dict, List, Optional, Any
from datetime import datetime

class RoomService:
    """Service for managing collaborative listening rooms"""
    
    def __init__(self, db_file: str):
        self.db_file = db_file
        self.socketio = None
    
    def init_socketio(self, socketio):
        """Initialize SocketIO for real-time broadcasts"""
        self.socketio = socketio
    
    def get_room_state(self, room_id: str) -> Optional[Dict]:
        """Get current state of a room"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("""
            SELECT r.*, COUNT(rm.id) as member_count
            FROM rooms r
            LEFT JOIN room_members rm ON r.id = rm.room_id
            WHERE r.id = ?
            GROUP BY r.id
        """, (room_id,))
        room = c.fetchone()
        conn.close()
        
        return dict(room) if room else None
    
    def get_queue(self, room_id: str) -> List[Dict]:
        """Get queue for a room"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("""
            SELECT rq.*, t.title, t.artist, t.filename, t.cover_filename,
                   u.display_name as added_by_name
            FROM room_queue rq
            JOIN tracks t ON rq.track_id = t.id
            JOIN users u ON rq.added_by_id = u.id
            WHERE rq.room_id = ?
            ORDER BY rq.sort_order ASC, rq.created_at ASC
        """, (room_id,))
        queue = [dict(row) for row in c.fetchall()]
        conn.close()
        
        return queue
    
    def get_members(self, room_id: str) -> List[Dict]:
        """Get members of a room"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("""
            SELECT u.id, u.display_name, u.avatar_url, u.nickname,
                   rm.joined_at
            FROM room_members rm
            JOIN users u ON rm.user_id = u.id
            WHERE rm.room_id = ?
            ORDER BY rm.joined_at ASC
        """, (room_id,))
        members = [dict(row) for row in c.fetchall()]
        conn.close()
        
        return members
    
    def join_room(self, room_id: str, user_id: int) -> bool:
        """Add a user to a room"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        # Check if room exists
        c.execute("SELECT id FROM rooms WHERE id = ?", (room_id,))
        if not c.fetchone():
            conn.close()
            return False
        
        try:
            c.execute("INSERT INTO room_members (room_id, user_id) VALUES (?, ?)", 
                     (room_id, user_id))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False
    
    def leave_room(self, room_id: str, user_id: int) -> bool:
        """Remove a user from a room"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        c.execute("DELETE FROM room_members WHERE room_id = ? AND user_id = ?", 
                 (room_id, user_id))
        conn.commit()
        conn.close()
        return True
    
    def add_to_queue(self, room_id: str, track_id: int, user_id: int) -> bool:
        """Add a track to room queue"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        # Verify membership
        c.execute("SELECT id FROM room_members WHERE room_id = ? AND user_id = ?", 
                 (room_id, user_id))
        if not c.fetchone():
            conn.close()
            return False
        
        # Get max sort order
        c.execute("SELECT MAX(sort_order) FROM room_queue WHERE room_id = ?", (room_id,))
        max_order = c.fetchone()[0] or 0
        
        c.execute("INSERT INTO room_queue (room_id, track_id, added_by_id, sort_order) VALUES (?, ?, ?, ?)",
                 (room_id, track_id, user_id, max_order + 1))
        conn.commit()
        conn.close()
        return True
    
    def play_next(self, room_id: str) -> Optional[Dict]:
        """Play next track in queue"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Get next track
        c.execute("""
            SELECT track_id FROM room_queue 
            WHERE room_id = ? 
            ORDER BY sort_order ASC, created_at ASC 
            LIMIT 1
        """, (room_id,))
        next_track = c.fetchone()
        
        if not next_track:
            conn.close()
            return None
        
        track_id = next_track[0]
        
        # Update room
        c.execute("UPDATE rooms SET current_track_id = ?, is_playing = 1, current_time = 0 WHERE id = ?", 
                 (track_id, room_id))
        
        # Remove from queue
        c.execute("DELETE FROM room_queue WHERE room_id = ? AND track_id = ?", 
                 (room_id, track_id))
        
        # Get track details
        c.execute("SELECT * FROM tracks WHERE id = ?", (track_id,))
        track = c.fetchone()
        
        conn.commit()
        conn.close()
        
        return dict(track) if track else None
    
    def sync_playback(self, room_id: str, current_time: float, is_playing: bool) -> bool:
        """Sync playback position for all room members"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        c.execute("UPDATE rooms SET current_time = ?, is_playing = ? WHERE id = ?",
                 (current_time, 1 if is_playing else 0, room_id))
        conn.commit()
        conn.close()
        return True
    
    def broadcast_room_update(self, room_id: str):
        """Broadcast room update via SocketIO"""
        if not self.socketio:
            return
        
        state = self.get_room_state(room_id)
        if state:
            self.socketio.emit('room_update', state, room=room_id)
