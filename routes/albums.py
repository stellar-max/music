# routes/albums.py - Album management routes

import os
import sqlite3
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, session, current_app
from common import login_required, get_current_user, allowed_file, DB_FILE

albums_bp = Blueprint('albums', __name__)

@albums_bp.route('', methods=['GET'])
def get_albums():
    """Get albums with optional filtering"""
    user_id = request.args.get('user_id', type=int)
    current_user = get_current_user()
    
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    query = """SELECT a.*, u.nickname, u.display_name, u.avatar_url,
              COALESCE(a.plays_count, 0) as plays_count,
              COALESCE(a.likes_count, 0) as likes_count
               FROM albums a 
               JOIN users u ON a.user_id = u.id 
               WHERE a.hidden = 0"""
    params = []
    if user_id:
        query += " AND a.user_id = ?"
        params.append(user_id)
    query += " ORDER BY a.is_pinned DESC, a.created_at DESC"
    c.execute(query, params)
    
    albums = []
    for row in c.fetchall():
        album = dict(row)
        if current_user:
            c.execute("SELECT id FROM album_likes WHERE user_id = ? AND album_id = ?", 
                     (current_user['id'], album['id']))
            album['is_liked'] = c.fetchone() is not None
        else:
            album['is_liked'] = False
        albums.append(album)
    
    conn.close()
    return jsonify(albums)

@albums_bp.route('', methods=['POST'])
@login_required
def create_album():
    """Create a new album"""
    if request.content_type and 'application/json' in request.content_type:
        data = request.get_json()
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        slug = data.get('slug', '').strip() or None
    else:
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        slug = request.form.get('slug', '').strip() or None
    
    if not title:
        return jsonify({'error': 'Title is required'}), 400
    
    cover_filename = None
    if 'cover' in request.files and request.files['cover'].filename:
        cover = request.files['cover']
        if allowed_file(cover.filename):
            cover_ext = cover.filename.rsplit('.', 1)[1].lower()
            cover_filename = f"{session['user_id']}_{int(datetime.now().timestamp())}_{uuid.uuid4().hex}.{cover_ext}"
            cover.save(os.path.join(current_app.config['UPLOAD_FOLDER'], cover_filename))
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("""INSERT INTO albums (user_id, title, description, slug, cover_filename) 
                     VALUES (?, ?, ?, ?, ?)""",
                  (session['user_id'], title, description, slug, cover_filename))
        conn.commit()
        album_id = c.lastrowid
        conn.close()
        return jsonify({'success': True, 'id': album_id})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Slug already exists'}), 400

@albums_bp.route('/<int:album_id>', methods=['PUT'])
@login_required
def update_album(album_id):
    """Update album details"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id, cover_filename FROM albums WHERE id = ?", (album_id,))
    album = c.fetchone()
    
    if not album or album[0] != session['user_id']:
        conn.close()
        return jsonify({'error': 'Forbidden'}), 403
    
    if request.content_type and 'application/json' in request.content_type:
        data = request.get_json()
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        slug = data.get('slug', '').strip() or None
    else:
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        slug = request.form.get('slug', '').strip() or None
    
    cover_filename = None
    if 'cover' in request.files and request.files['cover'].filename:
        cover = request.files['cover']
        if allowed_file(cover.filename):
            cover_ext = cover.filename.rsplit('.', 1)[1].lower()
            cover_filename = f"{session['user_id']}_{int(datetime.now().timestamp())}_{uuid.uuid4().hex}.{cover_ext}"
            cover.save(os.path.join(current_app.config['UPLOAD_FOLDER'], cover_filename))
            # Delete old cover
            if album[1]:
                old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], album[1])
                if os.path.exists(old_path):
                    os.remove(old_path)
    
    try:
        if cover_filename:
            c.execute("UPDATE albums SET title=?, description=?, slug=?, cover_filename=? WHERE id=?",
                      (title, description, slug, cover_filename, album_id))
        else:
            c.execute("UPDATE albums SET title=?, description=?, slug=? WHERE id=?",
                      (title, description, slug, album_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Slug already exists'}), 400

@albums_bp.route('/<int:album_id>', methods=['DELETE'])
@login_required
def delete_album(album_id):
    """Delete an album"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id, cover_filename FROM albums WHERE id = ?", (album_id,))
    album = c.fetchone()
    
    if not album or album[0] != session['user_id']:
        conn.close()
        return jsonify({'error': 'Forbidden'}), 403
    
    # Delete cover if exists
    if album[1]:
        path = os.path.join(current_app.config['UPLOAD_FOLDER'], album[1])
        if os.path.exists(path):
            os.remove(path)
    
    c.execute("DELETE FROM albums WHERE id = ?", (album_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@albums_bp.route('/<int:album_id>/tracks', methods=['GET'])
def get_album_tracks(album_id):
    """Get tracks in an album"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""SELECT t.*, at.sort_order, u.nickname,
                    COALESCE(t.plays_count, 0) as plays_count,
                    COALESCE(t.likes_count, 0) as likes_count
                 FROM tracks t 
                 JOIN album_tracks at ON t.id = at.track_id 
                 JOIN users u ON t.user_id = u.id
                 WHERE at.album_id = ? AND t.hidden = 0 
                 ORDER BY at.sort_order ASC, t.id ASC""", (album_id,))
    tracks = [dict(row) for row in c.fetchall()]
    
    # Check likes for each track
    current_user = get_current_user()
    for track in tracks:
        if current_user:
            c.execute("SELECT id FROM likes WHERE user_id = ? AND track_id = ?", 
                     (current_user['id'], track['id']))
            track['is_liked'] = c.fetchone() is not None
        else:
            track['is_liked'] = False
    
    conn.close()
    return jsonify(tracks)

@albums_bp.route('/<int:album_id>/tracks', methods=['POST'])
@login_required
def add_track_to_album(album_id):
    """Add a track to an album"""
    data = request.get_json()
    track_id = data.get('track_id')
    
    if not track_id:
        return jsonify({'error': 'track_id is required'}), 400
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Verify album ownership
    c.execute("SELECT user_id FROM albums WHERE id = ?", (album_id,))
    album = c.fetchone()
    if not album or album[0] != session['user_id']:
        conn.close()
        return jsonify({'error': 'Forbidden'}), 403
    
    # Verify track ownership
    c.execute("SELECT user_id FROM tracks WHERE id = ?", (track_id,))
    track = c.fetchone()
    if not track or track[0] != session['user_id']:
        conn.close()
        return jsonify({'error': 'Forbidden'}), 403
    
    try:
        c.execute("SELECT MAX(sort_order) FROM album_tracks WHERE album_id = ?", (album_id,))
        max_order = c.fetchone()[0] or 0
        c.execute("INSERT INTO album_tracks (album_id, track_id, sort_order) VALUES (?, ?, ?)",
                  (album_id, track_id, max_order + 1))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Track already in album'}), 400

@albums_bp.route('/<int:album_id>/tracks/<int:track_id>', methods=['DELETE'])
@login_required
def remove_track_from_album(album_id, track_id):
    """Remove a track from an album"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id FROM albums WHERE id = ?", (album_id,))
    album = c.fetchone()
    
    if not album or album[0] != session['user_id']:
        conn.close()
        return jsonify({'error': 'Forbidden'}), 403
    
    c.execute("DELETE FROM album_tracks WHERE album_id = ? AND track_id = ?", (album_id, track_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@albums_bp.route('/<int:album_id>/tracks/<int:track_id>/move', methods=['POST'])
@login_required
def move_track_in_album(album_id, track_id):
    """Move track order in album (up/down)"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id FROM albums WHERE id = ?", (album_id,))
    album = c.fetchone()
    
    if not album or album[0] != session['user_id']:
        conn.close()
        return jsonify({'error': 'Forbidden'}), 403
    
    data = request.get_json() or {}
    direction = data.get('direction', 'down')
    
    # Get current sort_order
    c.execute("SELECT sort_order FROM album_tracks WHERE album_id = ? AND track_id = ?", (album_id, track_id))
    current = c.fetchone()
    if not current:
        conn.close()
        return jsonify({'error': 'Track not in album'}), 404
    
    current_order = current[0]
    
    if direction == 'up':
        c.execute("""SELECT track_id, sort_order FROM album_tracks 
                     WHERE album_id = ? AND sort_order < ? 
                     ORDER BY sort_order DESC LIMIT 1""", (album_id, current_order))
        prev_track = c.fetchone()
        if prev_track:
            c.execute("UPDATE album_tracks SET sort_order = ? WHERE album_id = ? AND track_id = ?", 
                     (prev_track[1], album_id, track_id))
            c.execute("UPDATE album_tracks SET sort_order = ? WHERE album_id = ? AND track_id = ?", 
                     (current_order, album_id, prev_track[0]))
    else:  # down
        c.execute("""SELECT track_id, sort_order FROM album_tracks 
                     WHERE album_id = ? AND sort_order > ? 
                     ORDER BY sort_order ASC LIMIT 1""", (album_id, current_order))
        next_track = c.fetchone()
        if next_track:
            c.execute("UPDATE album_tracks SET sort_order = ? WHERE album_id = ? AND track_id = ?", 
                     (next_track[1], album_id, track_id))
            c.execute("UPDATE album_tracks SET sort_order = ? WHERE album_id = ? AND track_id = ?", 
                     (current_order, album_id, next_track[0]))
    
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@albums_bp.route('/<int:album_id>/like', methods=['POST'])
@login_required
def toggle_album_like(album_id):
    """Toggle album like status"""
    user_id = session['user_id']
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    try:
        # Check if album exists
        c.execute("SELECT id FROM albums WHERE id = ?", (album_id,))
        if not c.fetchone():
            conn.close()
            return jsonify({'error': 'Album not found'}), 404
        
        # Check existing like
        c.execute("SELECT id FROM album_likes WHERE user_id = ? AND album_id = ?", (user_id, album_id))
        like = c.fetchone()
        
        if like:
            c.execute("DELETE FROM album_likes WHERE id = ?", (like[0],))
            c.execute("UPDATE albums SET likes_count = CASE WHEN COALESCE(likes_count, 0) > 0 THEN likes_count - 1 ELSE 0 END WHERE id = ?", (album_id,))
            liked = False
        else:
            c.execute("INSERT INTO album_likes (user_id, album_id) VALUES (?, ?)", (user_id, album_id))
            c.execute("UPDATE albums SET likes_count = COALESCE(likes_count, 0) + 1 WHERE id = ?", (album_id,))
            liked = True
        
        conn.commit()
        
        # Get actual count
        c.execute("SELECT COUNT(*) FROM album_likes WHERE album_id = ?", (album_id,))
        actual_count = c.fetchone()[0] or 0
        c.execute("UPDATE albums SET likes_count = ? WHERE id = ?", (actual_count, album_id))
        conn.commit()
        
        conn.close()
        return jsonify({'success': True, 'liked': liked, 'likes_count': actual_count})
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"Error toggling album like: {e}")
        return jsonify({'error': str(e)}), 500

@albums_bp.route('/<int:album_id>/play', methods=['POST'])
def count_album_play(album_id):
    """Increment album play count"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE albums SET plays_count = COALESCE(plays_count, 0) + 1 WHERE id = ?", (album_id,))
    conn.commit()
    c.execute("SELECT COALESCE(plays_count, 0) FROM albums WHERE id = ?", (album_id,))
    count = c.fetchone()[0] or 0
    conn.close()
    return jsonify({'success': True, 'plays_count': count})