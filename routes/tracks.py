# routes/tracks.py
# Track management routes - CRUD operations

import os
import sqlite3
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.utils import secure_filename
from app import login_required, get_current_user, allowed_file, DB_FILE, MUTAGEN_AVAILABLE

tracks_bp = Blueprint('tracks', __name__)

@tracks_bp.route('', methods=['GET'])
def get_tracks():
    """Get tracks - with optional filtering"""
    show_hidden = request.args.get('show_hidden', 'false').lower() == 'true'
    user_id = request.args.get('user_id', type=int)
    track_id = request.args.get('id', type=int)
    current_user = get_current_user()
    
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get specific track by ID
    if track_id:
        if show_hidden and current_user and user_id == current_user['id']:
            c.execute("""SELECT t.*, u.nickname, u.display_name, u.avatar_url,
                        COALESCE(t.plays_count, 0) as plays_count,
                        COALESCE(t.likes_count, 0) as likes_count
                         FROM tracks t 
                         JOIN users u ON t.user_id = u.id 
                         WHERE t.id = ? AND t.user_id = ?""", (track_id, user_id))
        else:
            c.execute("""SELECT t.*, u.nickname, u.display_name, u.avatar_url,
                        COALESCE(t.plays_count, 0) as plays_count,
                        COALESCE(t.likes_count, 0) as likes_count
                         FROM tracks t 
                         JOIN users u ON t.user_id = u.id 
                         WHERE t.id = ? AND t.hidden = 0""", (track_id,))
        
        track = c.fetchone()
        conn.close()
        
        if not track:
            return jsonify([]), 200
        
        track_dict = dict(track)
        
        # Check if current user liked this track
        if current_user:
            c = conn.cursor() if conn else None
            if conn:
                c = conn.cursor()
                c.execute("SELECT id FROM likes WHERE user_id = ? AND track_id = ?", 
                         (current_user['id'], track_id))
                track_dict['is_liked'] = c.fetchone() is not None
                conn.close()
        else:
            track_dict['is_liked'] = False
        
        return jsonify([track_dict])
    
    # Get all tracks
    query = """SELECT t.*, u.nickname, u.display_name, u.avatar_url,
              COALESCE(t.plays_count, 0) as plays_count,
              COALESCE(t.likes_count, 0) as likes_count
               FROM tracks t 
               JOIN users u ON t.user_id = u.id 
               WHERE t.hidden = 0"""
    params = []
    
    if user_id:
        query += " AND t.user_id = ?"
        params.append(user_id)
    
    query += " ORDER BY COALESCE(t.sort_order, 999999) ASC, t.id ASC"
    c.execute(query, params)
    
    tracks = []
    for row in c.fetchall():
        track = dict(row)
        if current_user:
            c.execute("SELECT id FROM likes WHERE user_id = ? AND track_id = ?", 
                     (current_user['id'], track['id']))
            track['is_liked'] = c.fetchone() is not None
        else:
            track['is_liked'] = False
        tracks.append(track)
    
    conn.close()
    return jsonify(tracks)

@tracks_bp.route('', methods=['POST'])
@login_required
def upload_track():
    """Upload a new track"""
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file'}), 400
    
    audio = request.files['audio']
    cover = request.files.get('cover')
    title = request.form.get('title', '')
    artist = request.form.get('artist', '')
    lyrics = request.form.get('lyrics', '')
    slug = request.form.get('slug', '').strip() or None
    
    if audio and allowed_file(audio.filename):
        user_id = session['user_id']
        ext = audio.filename.rsplit('.', 1)[1].lower()
        audio_filename = f"{user_id}_{int(datetime.now().timestamp())}_{uuid.uuid4().hex}.{ext}"
        audio_path = os.path.join(current_app.config['UPLOAD_FOLDER'], audio_filename)
        audio.save(audio_path)
        
        cover_filename = None
        # Handle cover upload or extraction
        if cover and allowed_file(cover.filename):
            cover_ext = cover.filename.rsplit('.', 1)[1].lower()
            cover_filename = f"{user_id}_{int(datetime.now().timestamp())}_{uuid.uuid4().hex}.{cover_ext}"
            cover.save(os.path.join(current_app.config['UPLOAD_FOLDER'], cover_filename))
        elif MUTAGEN_AVAILABLE and audio_filename.lower().endswith('.mp3'):
            # Try to extract cover from MP3
            try:
                from mutagen.mp3 import MP3
                from mutagen.id3 import ID3, ID3NoHeaderError
                try:
                    audio_meta = MP3(audio_path, ID3=ID3)
                except ID3NoHeaderError:
                    audio_meta = MP3(audio_path)
                
                if audio_meta.tags:
                    apic = None
                    for key in audio_meta.tags.keys():
                        if key.startswith('APIC'):
                            apic = audio_meta.tags[key]
                            break
                    
                    if apic:
                        apic_data = apic.data if hasattr(apic, 'data') else None
                        if apic_data:
                            mime = getattr(apic, 'mime', 'image/jpeg')
                            ext = '.jpg'
                            if 'png' in mime.lower():
                                ext = '.png'
                            elif 'gif' in mime.lower():
                                ext = '.gif'
                            elif 'webp' in mime.lower():
                                ext = '.webp'
                            
                            cover_filename = audio_filename.rsplit('.', 1)[0] + ext
                            cover_path = os.path.join(current_app.config['UPLOAD_FOLDER'], cover_filename)
                            with open(cover_path, 'wb') as f:
                                f.write(apic_data)
            except Exception as e:
                print(f"Error extracting cover: {e}")
        
        if not title:
            title = audio_filename.rsplit('.', 1)[0]
        
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        try:
            c.execute("SELECT MAX(sort_order) FROM tracks WHERE user_id = ?", (user_id,))
            max_order = c.fetchone()[0] or 0
            c.execute("""INSERT INTO tracks (user_id, title, artist, filename, cover_filename, lyrics, sort_order, hidden, slug) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)""",
                      (user_id, title, artist, audio_filename, cover_filename or '', lyrics, max_order + 1, slug))
            conn.commit()
            track_id = c.lastrowid
            conn.close()
            return jsonify({'success': True, 'id': track_id})
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'error': 'Slug already exists'}), 400
    
    return jsonify({'error': 'Invalid file'}), 400

@tracks_bp.route('/<int:track_id>', methods=['PUT'])
@login_required
def update_track(track_id):
    """Update track metadata"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Verify ownership
    c.execute("SELECT * FROM tracks WHERE id = ?", (track_id,))
    track = c.fetchone()
    if not track or track[1] != session['user_id']:
        conn.close()
        return jsonify({'error': 'Forbidden'}), 403
    
    title = request.form.get('title')
    artist = request.form.get('artist')
    lyrics = request.form.get('lyrics')
    slug = request.form.get('slug', '').strip() or None
    
    query = "UPDATE tracks SET title=?, artist=?, lyrics=?, slug=?"
    params = [title, artist, lyrics, slug]
    
    # Handle file updates if provided
    if 'audio' in request.files and request.files['audio'].filename:
        audio = request.files['audio']
        if allowed_file(audio.filename):
            ext = audio.filename.rsplit('.', 1)[1].lower()
            audio_filename = f"{session['user_id']}_{int(datetime.now().timestamp())}_{uuid.uuid4().hex}.{ext}"
            audio.save(os.path.join(current_app.config['UPLOAD_FOLDER'], audio_filename))
            # Cleanup old file
            if track[3]:
                old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], track[3])
                if os.path.exists(old_path):
                    os.remove(old_path)
            query += ", filename=?"
            params.append(audio_filename)
    
    if 'cover' in request.files and request.files['cover'].filename:
        cover = request.files['cover']
        if allowed_file(cover.filename):
            cover_ext = cover.filename.rsplit('.', 1)[1].lower()
            cover_filename = f"{session['user_id']}_{int(datetime.now().timestamp())}_{uuid.uuid4().hex}.{cover_ext}"
            cover.save(os.path.join(current_app.config['UPLOAD_FOLDER'], cover_filename))
            # Cleanup old cover
            if track[4]:
                old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], track[4])
                if os.path.exists(old_path):
                    os.remove(old_path)
            query += ", cover_filename=?"
            params.append(cover_filename)
    
    query += " WHERE id=?"
    params.append(track_id)
    
    try:
        c.execute(query, params)
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Slug already exists'}), 400

@tracks_bp.route('/<int:track_id>', methods=['DELETE'])
@login_required
def delete_track(track_id):
    """Delete a track"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id, filename, cover_filename FROM tracks WHERE id = ?", (track_id,))
    track = c.fetchone()
    
    if not track or track[0] != session['user_id']:
        conn.close()
        return jsonify({'error': 'Forbidden'}), 403
    
    # Delete files
    if track[1]:
        path = os.path.join(current_app.config['UPLOAD_FOLDER'], track[1])
        if os.path.exists(path):
            os.remove(path)
    if track[2]:
        path = os.path.join(current_app.config['UPLOAD_FOLDER'], track[2])
        if os.path.exists(path):
            os.remove(path)
    
    c.execute("DELETE FROM tracks WHERE id = ?", (track_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@tracks_bp.route('/<int:track_id>/like', methods=['GET', 'POST'])
def toggle_like(track_id):
    """Get or toggle track like status"""
    current_user = get_current_user()
    
    if request.method == 'GET':
        liked = False
        if current_user:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT id FROM likes WHERE user_id = ? AND track_id = ?", 
                     (current_user['id'], track_id))
            liked = c.fetchone() is not None
            conn.close()
        
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT COALESCE(likes_count, 0) FROM tracks WHERE id = ?", (track_id,))
        count = c.fetchone()[0] or 0
        conn.close()
        
        return jsonify({'success': True, 'liked': liked, 'likes_count': count})
    
    # POST - toggle like
    if not current_user:
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Please login to like tracks',
            'auth_url': f'https://t.me/swagplayerobot?start=auth'
        }), 401
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute("SELECT id FROM likes WHERE user_id = ? AND track_id = ?", 
             (current_user['id'], track_id))
    like = c.fetchone()
    
    if like:
        c.execute("DELETE FROM likes WHERE id = ?", (like[0],))
        c.execute("UPDATE tracks SET likes_count = COALESCE(likes_count, 0) - 1 WHERE id = ?", (track_id,))
        liked = False
    else:
        c.execute("INSERT INTO likes (user_id, track_id) VALUES (?, ?)", 
                 (current_user['id'], track_id))
        c.execute("UPDATE tracks SET likes_count = COALESCE(likes_count, 0) + 1 WHERE id = ?", (track_id,))
        liked = True
    
    conn.commit()
    c.execute("SELECT COALESCE(likes_count, 0) FROM tracks WHERE id = ?", (track_id,))
    count = c.fetchone()[0] or 0
    conn.close()
    
    return jsonify({'success': True, 'liked': liked, 'likes_count': count})

@tracks_bp.route('/<int:track_id>/play', methods=['POST'])
def count_play(track_id):
    """Increment track play count"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute("UPDATE tracks SET plays_count = COALESCE(plays_count, 0) + 1 WHERE id = ?", (track_id,))
    
    current_user = get_current_user()
    if current_user:
        c.execute("""INSERT INTO track_plays (user_id, track_id, play_count, last_played_at) 
                     VALUES (?, ?, 1, datetime('now'))
                     ON CONFLICT(user_id, track_id) DO UPDATE SET 
                     play_count = play_count + 1,
                     last_played_at = datetime('now')""", 
                  (current_user['id'], track_id))
    
    conn.commit()
    c.execute("SELECT COALESCE(plays_count, 0) FROM tracks WHERE id = ?", (track_id,))
    count = c.fetchone()[0] or 0
    conn.close()
    return jsonify({'success': True, 'plays_count': count})

@tracks_bp.route('/<int:track_id>/toggle-visibility', methods=['POST'])
@login_required
def toggle_visibility(track_id):
    """Toggle track visibility (hide/show)"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id FROM tracks WHERE id = ?", (track_id,))
    track = c.fetchone()
    
    if not track or track[0] != session['user_id']:
        conn.close()
        return jsonify({'error': 'Forbidden'}), 403
    
    data = request.get_json() or {}
    hidden = 1 if data.get('hidden') else 0
    c.execute("UPDATE tracks SET hidden = ? WHERE id = ?", (hidden, track_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@tracks_bp.route('/extract-metadata', methods=['POST'])
def extract_metadata():
    """Extract metadata from audio file (title, artist, cover)"""
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file'}), 400
    
    audio_file = request.files['audio']
    if not audio_file or not allowed_file(audio_file.filename):
        return jsonify({'error': 'Invalid file'}), 400
    
    result = {'title': '', 'artist': '', 'cover': ''}
    
    if MUTAGEN_AVAILABLE and audio_file.filename.lower().endswith('.mp3'):
        try:
            temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp_' + secure_filename(audio_file.filename))
            audio_file.save(temp_path)
            
            try:
                from mutagen.mp3 import MP3
                from mutagen.id3 import ID3, ID3NoHeaderError
                try:
                    audio = MP3(temp_path, ID3=ID3)
                except ID3NoHeaderError:
                    audio = MP3(temp_path)
                
                if audio.tags:
                    if 'TIT2' in audio.tags:
                        result['title'] = str(audio.tags['TIT2'][0])
                    if 'TPE1' in audio.tags:
                        result['artist'] = str(audio.tags['TPE1'][0])
                    
                    apic = None
                    for key in audio.tags.keys():
                        if key.startswith('APIC'):
                            apic = audio.tags[key]
                            break
                    
                    if apic:
                        apic_data = apic.data if hasattr(apic, 'data') else None
                        if apic_data:
                            import base64
                            mime = getattr(apic, 'mime', 'image/jpeg')
                            cover_base64 = base64.b64encode(apic_data).decode('utf-8')
                            result['cover'] = f'data:{mime};base64,{cover_base64}'
            except Exception as e:
                print(f"Error extracting metadata: {e}")
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        except Exception as e:
            print(f"Error processing file: {e}")
    
    return jsonify(result)
