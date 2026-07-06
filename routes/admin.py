# routes/admin.py
# Admin panel routes

import os
import sqlite3
from flask import Blueprint, request, jsonify, session, render_template, redirect, current_app
from werkzeug.security import check_password_hash
from app import admin_required, login_required, DB_FILE

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT * FROM admins WHERE username = ?", (username,))
        admin = c.fetchone()
        conn.close()
        
        if admin and check_password_hash(admin[2], password):
            session['admin'] = True
            session['admin_username'] = username
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    
    return render_template('admin_login.html')

@admin_bp.route('/logout', methods=['POST'])
def admin_logout():
    """Admin logout"""
    session.pop('admin', None)
    session.pop('admin_username', None)
    return jsonify({'success': True})

@admin_bp.route('', methods=['GET'])
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    return render_template('admin_new.html')

@admin_bp.route('/tracks', methods=['GET'])
@admin_required
def get_tracks():
    """Get all tracks for admin"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""SELECT t.*, u.nickname, u.display_name,
                 GROUP_CONCAT(a.title, ', ') as album_names
                 FROM tracks t 
                 JOIN users u ON t.user_id = u.id 
                 LEFT JOIN album_tracks at ON t.id = at.track_id
                 LEFT JOIN albums a ON at.album_id = a.id
                 GROUP BY t.id
                 ORDER BY t.is_pinned DESC, t.created_at DESC""")
    tracks = []
    for row in c.fetchall():
        track = dict(row)
        track['is_pinned'] = bool(track.get('is_pinned', 0))
        tracks.append(track)
    conn.close()
    return jsonify(tracks)

@admin_bp.route('/albums', methods=['GET'])
@admin_required
def get_albums():
    """Get all albums for admin"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""SELECT a.*, u.nickname, u.display_name 
                 FROM albums a 
                 JOIN users u ON a.user_id = u.id 
                 ORDER BY a.is_pinned DESC, a.created_at DESC""")
    albums = []
    for row in c.fetchall():
        album = dict(row)
        album['is_pinned'] = bool(album.get('is_pinned', 0))
        albums.append(album)
    conn.close()
    return jsonify(albums)

@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    """Get all users for admin"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users ORDER BY created_at DESC")
    users = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(users)

@admin_bp.route('/tracks/<int:track_id>/toggle-visibility', methods=['POST'])
@admin_required
def toggle_track_visibility(track_id):
    """Toggle track visibility (admin)"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    data = request.get_json() or {}
    hidden = 1 if data.get('hidden') else 0
    c.execute("UPDATE tracks SET hidden = ? WHERE id = ?", (hidden, track_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@admin_bp.route('/tracks/<int:track_id>', methods=['DELETE'])
@admin_required
def delete_track(track_id):
    """Delete a track (admin)"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT filename, cover_filename FROM tracks WHERE id = ?", (track_id,))
    track = c.fetchone()
    
    if not track:
        conn.close()
        return jsonify({'error': 'Track not found'}), 404
    
    # Delete files
    if track[0]:
        path = os.path.join(current_app.config['UPLOAD_FOLDER'], track[0])
        if os.path.exists(path):
            os.remove(path)
    if track[1]:
        path = os.path.join(current_app.config['UPLOAD_FOLDER'], track[1])
        if os.path.exists(path):
            os.remove(path)
    
    c.execute("DELETE FROM tracks WHERE id = ?", (track_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@admin_bp.route('/albums/<int:album_id>/toggle-visibility', methods=['POST'])
@admin_required
def toggle_album_visibility(album_id):
    """Toggle album visibility (admin)"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    data = request.get_json() or {}
    hidden = 1 if data.get('hidden') else 0
    c.execute("UPDATE albums SET hidden = ? WHERE id = ?", (hidden, album_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@admin_bp.route('/albums/<int:album_id>', methods=['DELETE'])
@admin_required
def delete_album(album_id):
    """Delete an album (admin)"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT cover_filename FROM albums WHERE id = ?", (album_id,))
    album = c.fetchone()
    
    if not album:
        conn.close()
        return jsonify({'error': 'Album not found'}), 404
    
    if album[0]:
        path = os.path.join(current_app.config['UPLOAD_FOLDER'], album[0])
        if os.path.exists(path):
            os.remove(path)
    
    c.execute("DELETE FROM albums WHERE id = ?", (album_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@admin_bp.route('/tracks/<int:track_id>/pin', methods=['POST'])
@admin_required
def toggle_track_pin(track_id):
    """Pin/unpin a track (admin)"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    data = request.get_json() or {}
    is_pinned = 1 if data.get('is_pinned') else 0
    c.execute("UPDATE tracks SET is_pinned = ? WHERE id = ?", (is_pinned, track_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'is_pinned': bool(is_pinned)})

@admin_bp.route('/albums/<int:album_id>/pin', methods=['POST'])
@admin_required
def toggle_album_pin(album_id):
    """Pin/unpin an album (admin)"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    data = request.get_json() or {}
    is_pinned = 1 if data.get('is_pinned') else 0
    c.execute("UPDATE albums SET is_pinned = ? WHERE id = ?", (is_pinned, album_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'is_pinned': bool(is_pinned)})
