# app.py - Main Application Entry Point
# Clean, modular, with Socket.IO support

import os
import sqlite3
import hmac
import hashlib
import json
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

# Configuration
UPLOAD_FOLDER = 'uploads'
DB_FILE = 'music.db'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'jpg', 'jpeg', 'png'}
TELEGRAM_BOT_TOKEN = os.environ.get('BOT_TOKEN', '')

# Check for mutagen
try:
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3NoHeaderError, ID3, TIT2, TPE1, APIC
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DB_FILE'] = DB_FILE
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def init_db():
    """Initialize database with all required tables"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  telegram_id INTEGER UNIQUE,
                  username TEXT,
                  first_name TEXT,
                  last_name TEXT,
                  avatar_url TEXT,
                  nickname TEXT UNIQUE,
                  display_name TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Tracks table
    c.execute('''CREATE TABLE IF NOT EXISTS tracks
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  title TEXT,
                  artist TEXT,
                  filename TEXT,
                  cover_filename TEXT,
                  lyrics TEXT,
                  sort_order INTEGER DEFAULT 0,
                  hidden INTEGER DEFAULT 0,
                  slug TEXT,
                  is_pinned INTEGER DEFAULT 0,
                  plays_count INTEGER DEFAULT 0,
                  likes_count INTEGER DEFAULT 0,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users(id))''')
    
    # Albums table
    c.execute('''CREATE TABLE IF NOT EXISTS albums
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  title TEXT,
                  description TEXT,
                  cover_filename TEXT,
                  slug TEXT UNIQUE,
                  hidden INTEGER DEFAULT 0,
                  is_pinned INTEGER DEFAULT 0,
                  plays_count INTEGER DEFAULT 0,
                  likes_count INTEGER DEFAULT 0,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users(id))''')
    
    # Album likes
    c.execute('''CREATE TABLE IF NOT EXISTS album_likes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  album_id INTEGER,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users(id),
                  FOREIGN KEY (album_id) REFERENCES albums(id),
                  UNIQUE(user_id, album_id))''')
    
    # Album tracks mapping
    c.execute('''CREATE TABLE IF NOT EXISTS album_tracks
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  album_id INTEGER,
                  track_id INTEGER,
                  sort_order INTEGER DEFAULT 0,
                  FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE,
                  FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE,
                  UNIQUE(album_id, track_id))''')
    
    # Admins table
    c.execute('''CREATE TABLE IF NOT EXISTS admins
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  password_hash TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Auth tokens for browser login
    c.execute('''CREATE TABLE IF NOT EXISTS auth_tokens
                 (token TEXT PRIMARY KEY,
                  telegram_id INTEGER,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  expires_at TIMESTAMP)''')
    
    # Track likes
    c.execute('''CREATE TABLE IF NOT EXISTS likes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  track_id INTEGER,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users(id),
                  FOREIGN KEY (track_id) REFERENCES tracks(id),
                  UNIQUE(user_id, track_id))''')
    
    # Track plays tracking
    c.execute('''CREATE TABLE IF NOT EXISTS track_plays
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  track_id INTEGER,
                  play_count INTEGER DEFAULT 1,
                  last_played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users(id),
                  FOREIGN KEY (track_id) REFERENCES tracks(id),
                  UNIQUE(user_id, track_id))''')
    
    # Rooms for collaborative listening
    c.execute('''CREATE TABLE IF NOT EXISTS rooms
                 (id TEXT PRIMARY KEY,
                  name TEXT NOT NULL,
                  host_id INTEGER NOT NULL,
                  current_track_id INTEGER,
                  is_playing INTEGER DEFAULT 0,
                  current_time REAL DEFAULT 0.0,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (host_id) REFERENCES users(id))''')
    
    # Room members
    c.execute('''CREATE TABLE IF NOT EXISTS room_members
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  room_id TEXT,
                  user_id INTEGER,
                  joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
                  FOREIGN KEY (user_id) REFERENCES users(id),
                  UNIQUE(room_id, user_id))''')
    
    # Room queue
    c.execute('''CREATE TABLE IF NOT EXISTS room_queue
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  room_id TEXT,
                  track_id INTEGER,
                  added_by_id INTEGER,
                  sort_order INTEGER DEFAULT 0,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
                  FOREIGN KEY (track_id) REFERENCES tracks(id),
                  FOREIGN KEY (added_by_id) REFERENCES users(id))''')
    
    # Create indexes
    c.execute("CREATE INDEX IF NOT EXISTS idx_tracks_user_id ON tracks(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_tracks_slug ON tracks(slug)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_albums_user_id ON albums(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_albums_slug ON albums(slug)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_users_nickname ON users(nickname)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_room_members_room ON room_members(room_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_room_queue_room ON room_queue(room_id)")
    
    # Create default admin
    c.execute("SELECT COUNT(*) FROM admins")
    if c.fetchone()[0] == 0:
        admin_hash = generate_password_hash('admin123')
        c.execute("INSERT INTO admins (username, password_hash) VALUES (?, ?)", ('admin', admin_hash))
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully")

init_db()

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_current_user():
    """Get current user from session"""
    user_id = session.get('user_id')
    if not user_id:
        return None
    
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    
    return dict(user) if user else None

def verify_telegram_webapp_data(init_data):
    """Verify Telegram Web App data authenticity"""
    try:
        if not init_data:
            return None
            
        from urllib.parse import parse_qsl
        parsed_data = dict(parse_qsl(init_data))
        
        if 'hash' not in parsed_data:
            return None
        received_hash = parsed_data.pop('hash')
        
        secret_key = hmac.new(
            key=b"WebAppData",
            msg=TELEGRAM_BOT_TOKEN.encode(),
            digestmod=hashlib.sha256
        ).digest()
        
        data_check_string = '\n'.join(f"{k}={v}" for k, v in sorted(parsed_data.items()))
        calculated_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode('utf-8'),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        if calculated_hash != received_hash:
            return None
        
        if 'user' in parsed_data:
            return json.loads(parsed_data['user'])
        return None
    except Exception as e:
        print(f"Error verifying Telegram data: {e}")
        return None

# ============================================================================
# AUTHENTICATION DECORATORS
# ============================================================================

def login_required(f):
    """Decorator to require user authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin' not in session or not session['admin']:
            return redirect('/admin/login')
        return f(*args, **kwargs)
    return decorated_function

# ============================================================================
# MAIN ROUTES
# ============================================================================

@app.route('/')
def index():
    """Main page - unified library view"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    search_query = request.args.get('q', '').strip()
    current_user = get_current_user()
    
    # Get public tracks
    tracks_query = """SELECT t.*, u.nickname, u.display_name, u.avatar_url,
                        COALESCE(t.plays_count, 0) as plays_count,
                        COALESCE(t.likes_count, 0) as likes_count
                 FROM tracks t 
                 JOIN users u ON t.user_id = u.id 
                 WHERE t.hidden = 0"""
    tracks_params = []
    
    if search_query:
        tracks_query += " AND (t.title LIKE ? OR t.artist LIKE ?)"
        search_term = f"%{search_query}%"
        tracks_params.extend([search_term, search_term])
        
    tracks_query += " ORDER BY t.is_pinned DESC, t.created_at DESC LIMIT 50"
    
    c.execute(tracks_query, tracks_params)
    tracks_rows = c.fetchall()
    
    tracks = []
    for row in tracks_rows:
        track = dict(row)
        if current_user:
            c.execute("SELECT id FROM likes WHERE user_id = ? AND track_id = ?", 
                     (current_user['id'], track['id']))
            track['is_liked'] = c.fetchone() is not None
        else:
            track['is_liked'] = False
        tracks.append(track)
    
    # Get public albums
    albums_query = """SELECT a.*, u.nickname, u.display_name, u.avatar_url,
                        COALESCE(a.plays_count, 0) as plays_count,
                        COALESCE(a.likes_count, 0) as likes_count
                 FROM albums a 
                 JOIN users u ON a.user_id = u.id 
                 WHERE a.hidden = 0"""
    albums_params = []
    
    if search_query:
        albums_query += " AND (a.title LIKE ? OR a.description LIKE ?)"
        search_term = f"%{search_query}%"
        albums_params.extend([search_term, search_term])
        
    albums_query += " ORDER BY a.is_pinned DESC, a.created_at DESC LIMIT 50"
    
    c.execute(albums_query, albums_params)
    albums_rows = c.fetchall()
    
    albums = []
    for row in albums_rows:
        album = dict(row)
        if current_user:
            c.execute("SELECT id FROM album_likes WHERE user_id = ? AND album_id = ?", 
                     (current_user['id'], album['id']))
            album['is_liked'] = c.fetchone() is not None
        else:
            album['is_liked'] = False
        albums.append(album)
    
    conn.close()
    return render_template('unified.html', 
                          tracks=tracks, 
                          albums=albums, 
                          current_user=current_user,
                          search_query=search_query,
                          mode='library')

@app.route('/app')
def app_page():
    """Telegram Web App - main application page"""
    init_data = request.args.get('tgWebAppData', '')
    return render_template('app.html', shared_track=None, shared_mode=False, init_data=init_data)

@app.route('/track/<track_identifier>')
def share_track(track_identifier):
    """Public track sharing page"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    current_user = get_current_user()
    
    if track_identifier.isdigit():
        c.execute("""SELECT t.*, u.nickname, u.display_name, u.avatar_url,
                        COALESCE(t.plays_count, 0) as plays_count,
                        COALESCE(t.likes_count, 0) as likes_count
                     FROM tracks t 
                     JOIN users u ON t.user_id = u.id 
                     WHERE t.id = ? AND t.hidden = 0""", (int(track_identifier),))
    else:
        c.execute("""SELECT t.*, u.nickname, u.display_name, u.avatar_url,
                        COALESCE(t.plays_count, 0) as plays_count,
                        COALESCE(t.likes_count, 0) as likes_count
                     FROM tracks t 
                     JOIN users u ON t.user_id = u.id 
                     WHERE t.slug = ? AND t.hidden = 0""", (track_identifier,))
        
    row = c.fetchone()
    
    if not row:
        conn.close()
        return "Track not found", 404
        
    track = dict(row)
    
    if current_user:
        c.execute("SELECT id FROM likes WHERE user_id = ? AND track_id = ?", 
                 (current_user['id'], track['id']))
        track['is_liked'] = c.fetchone() is not None
    else:
        track['is_liked'] = False
    
    conn.close()
    title = f"{track['artist']} - {track['title']}"
    return render_template('unified.html', 
                          shared_track=track, 
                          current_user=current_user,
                          page_title=title,
                          mode='player')

@app.route('/album/<album_identifier>')
def share_album(album_identifier):
    """Public album sharing page"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    current_user = get_current_user()
    
    if album_identifier.isdigit():
        c.execute("""SELECT a.*, u.nickname, u.display_name, u.avatar_url,
                        COALESCE(a.plays_count, 0) as plays_count,
                        COALESCE(a.likes_count, 0) as likes_count
                     FROM albums a 
                     JOIN users u ON a.user_id = u.id 
                     WHERE a.id = ? AND a.hidden = 0""", (int(album_identifier),))
    else:
        c.execute("""SELECT a.*, u.nickname, u.display_name, u.avatar_url,
                        COALESCE(a.plays_count, 0) as plays_count,
                        COALESCE(a.likes_count, 0) as likes_count
                     FROM albums a 
                     JOIN users u ON a.user_id = u.id 
                     WHERE a.slug = ? AND a.hidden = 0""", (album_identifier,))
    
    album = c.fetchone()
    if not album:
        conn.close()
        return "Album not found", 404
    
    album = dict(album)
    
    if current_user:
        c.execute("SELECT id FROM album_likes WHERE user_id = ? AND album_id = ?", 
                 (current_user['id'], album['id']))
        album['is_liked'] = c.fetchone() is not None
    else:
        album['is_liked'] = False
    
    # Get album tracks
    c.execute("""SELECT t.*, at.sort_order, u.nickname,
                    COALESCE(t.plays_count, 0) as plays_count,
                    COALESCE(t.likes_count, 0) as likes_count
                 FROM tracks t 
                 JOIN album_tracks at ON t.id = at.track_id 
                 JOIN users u ON t.user_id = u.id
                 WHERE at.album_id = ? AND t.hidden = 0 
                 ORDER BY at.sort_order ASC, t.id ASC""", (album['id'],))
    tracks = [dict(row) for row in c.fetchall()]
    
    for track in tracks:
        if current_user:
            c.execute("SELECT id FROM likes WHERE user_id = ? AND track_id = ?", 
                     (current_user['id'], track['id']))
            track['is_liked'] = c.fetchone() is not None
        else:
            track['is_liked'] = False
    
    conn.close()
    
    return render_template('unified.html', 
                          shared_album=album, 
                          album_tracks=tracks,
                          current_user=current_user,
                          page_title=album['title'],
                          mode='player')

@app.route('/user/<nickname>')
def user_library(nickname):
    """Public user library page"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("SELECT * FROM users WHERE nickname = ?", (nickname,))
    user = c.fetchone()
    if not user:
        return "User not found", 404
    
    user = dict(user)
    
    c.execute("""SELECT * FROM tracks 
                 WHERE user_id = ? AND hidden = 0 
                 ORDER BY sort_order ASC, created_at DESC""", (user['id'],))
    tracks = [dict(row) for row in c.fetchall()]
    
    c.execute("""SELECT * FROM albums 
                 WHERE user_id = ? AND hidden = 0 
                 ORDER BY created_at DESC""", (user['id'],))
    albums = [dict(row) for row in c.fetchall()]
    
    conn.close()
    return render_template('library.html', user=user, tracks=tracks, albums=albums)

@app.route('/rooms')
def rooms_page():
    """Collaborative rooms page"""
    current_user = get_current_user()
    if not current_user:
        return redirect('/')
    
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("""
        SELECT r.*, COUNT(rm.id) as member_count,
               u.display_name as host_name
        FROM rooms r
        JOIN users u ON r.host_id = u.id
        LEFT JOIN room_members rm ON r.id = rm.room_id
        GROUP BY r.id
        ORDER BY r.created_at DESC
    """)
    rooms = [dict(row) for row in c.fetchall()]
    
    conn.close()
    return render_template('rooms.html', rooms=rooms, current_user=current_user)

@app.route('/room/<room_id>')
def room_detail(room_id):
    """Individual room page with player"""
    current_user = get_current_user()
    if not current_user:
        return redirect('/')
    
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("SELECT * FROM rooms WHERE id = ?", (room_id,))
    room = c.fetchone()
    if not room:
        conn.close()
        return "Room not found", 404
    
    room = dict(room)
    
    # Check membership
    c.execute("SELECT id FROM room_members WHERE room_id = ? AND user_id = ?", 
             (room_id, current_user['id']))
    is_member = c.fetchone() is not None
    
    # Get current track
    current_track = None
    if room.get('current_track_id'):
        c.execute("SELECT * FROM tracks WHERE id = ?", (room['current_track_id'],))
        current_track = c.fetchone()
        current_track = dict(current_track) if current_track else None
    
    # Get queue
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
    
    # Get members
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
    
    return render_template('room_detail.html',
                          room=room,
                          current_track=current_track,
                          queue=queue,
                          members=members,
                          is_member=is_member,
                          current_user=current_user)

# ============================================================================
# STATIC FILE ROUTES
# ============================================================================

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    try:
        upload_folder = app.config['UPLOAD_FOLDER']
        file_path = os.path.join(upload_folder, filename)
        
        if not os.path.exists(file_path):
            return "File not found", 404
        
        # Determine MIME type
        mime_type = None
        if filename.lower().endswith(('.jpg', '.jpeg')):
            mime_type = 'image/jpeg'
        elif filename.lower().endswith('.png'):
            mime_type = 'image/png'
        elif filename.lower().endswith('.mp3'):
            mime_type = 'audio/mpeg'
        elif filename.lower().endswith('.wav'):
            mime_type = 'audio/wav'
        elif filename.lower().endswith('.ogg'):
            mime_type = 'audio/ogg'
        
        response = send_from_directory(upload_folder, filename)
        if mime_type:
            response.headers['Content-Type'] = mime_type
        
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        
        return response
    except Exception as e:
        print(f"Error serving file {filename}: {e}")
        return f"Error serving file: {str(e)}", 500

@app.route('/static/<path:filename>')
def static_file(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

@app.route('/favicon.ico')
def favicon():
    """Return empty for favicon"""
    return '', 204

@app.route('/admin/login')
def admin_login_page():
    """Admin login page"""
    return render_template('admin_login.html')

@app.route('/admin')
def admin_page():
    """Admin dashboard page"""
    if 'admin' not in session or not session['admin']:
        return redirect('/admin/login')
    return render_template('admin_new.html')

# ============================================================================
# REGISTER BLUEPRINTS
# ============================================================================

from routes.auth import auth_bp
from routes.tracks import tracks_bp
from routes.albums import albums_bp
from routes.admin import admin_bp
from routes.rooms import rooms_bp

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(tracks_bp, url_prefix='/api/tracks')
app.register_blueprint(albums_bp, url_prefix='/api/albums')
app.register_blueprint(admin_bp, url_prefix='/admin/api')
app.register_blueprint(rooms_bp, url_prefix='/api/rooms')

# ============================================================================
# SOCKET.IO EVENTS
# ============================================================================

from services.room_service import RoomService

room_service = RoomService(DB_FILE)
room_service.init_socketio(socketio)

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    user = get_current_user()
    if user:
        print(f"User {user['display_name']} connected")
        emit('connected', {'user_id': user['id']})
    else:
        emit('connected', {'user_id': None})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    user = get_current_user()
    if user:
        print(f"User {user['display_name']} disconnected")

@socketio.on('join_room')
def handle_join_room(data):
    """Join a collaborative room"""
    room_id = data.get('room_id')
    user = get_current_user()
    
    if not user:
        emit('error', {'message': 'Authentication required'})
        return
    
    success = room_service.join_room(room_id, user['id'])
    if success:
        join_room(room_id)
        emit('room_joined', {'room_id': room_id, 'user': user}, room=room_id)
        room_state = room_service.get_room_state(room_id)
        if room_state:
            emit('room_state', room_state, room=room_id)
    else:
        emit('error', {'message': 'Could not join room'})

@socketio.on('leave_room')
def handle_leave_room(data):
    """Leave a collaborative room"""
    room_id = data.get('room_id')
    user = get_current_user()
    
    if not user:
        return
    
    leave_room(room_id)
    room_service.leave_room(room_id, user['id'])
    emit('room_left', {'room_id': room_id, 'user_id': user['id']}, room=room_id)

@socketio.on('add_to_queue')
def handle_add_to_queue(data):
    """Add a track to room queue"""
    room_id = data.get('room_id')
    track_id = data.get('track_id')
    user = get_current_user()
    
    if not user:
        emit('error', {'message': 'Authentication required'})
        return
    
    success = room_service.add_to_queue(room_id, track_id, user['id'])
    if success:
        emit('queue_updated', room_service.get_queue(room_id), room=room_id)
    else:
        emit('error', {'message': 'Could not add to queue'})

@socketio.on('play_next')
def handle_play_next(data):
    """Play next track in queue"""
    room_id = data.get('room_id')
    user = get_current_user()
    
    if not user:
        return
    
    track = room_service.play_next(room_id)
    if track:
        emit('track_changed', {
            'track': track,
            'current_time': 0.0,
            'is_playing': True
        }, room=room_id)
        emit('queue_updated', room_service.get_queue(room_id), room=room_id)

@socketio.on('sync_playback')
def handle_sync_playback(data):
    """Sync playback position for all room members"""
    room_id = data.get('room_id')
    current_time = data.get('current_time', 0.0)
    is_playing = data.get('is_playing', False)
    
    room_service.sync_playback(room_id, current_time, is_playing)
    emit('playback_sync', {
        'current_time': current_time,
        'is_playing': is_playing
    }, room=room_id, include_self=False)

# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.environ.get('PORT', 5024))
    host = os.environ.get('HOST', '127.0.0.1')
    
    socketio.run(app, debug=debug_mode, port=port, host=host)

def ensure_valid_db():
    """Check if music.db is valid SQLite, delete and recreate if corrupt."""
    db_file = 'music.db'
    if not os.path.exists(db_file):
        return  # No file, will be created later
    
    try:
        # Try to open and run a simple query
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master LIMIT 1")
        c.fetchone()
        conn.close()
    except sqlite3.DatabaseError:
        # File exists but is corrupt
        print(f"⚠️ Database file '{db_file}' is corrupt. Deleting...")
        os.remove(db_file)
        print("✅ Removed corrupt database. It will be recreated on init.")
    except Exception as e:
        print(f"⚠️ Unexpected error: {e}")
