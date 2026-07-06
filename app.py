# app.py - Main Application Entry Point
# Clean, modular, with Socket.IO support and auto-healing database

# app.py - Main Application Entry Point

import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

# Import everything from common
from common import (
    DB_FILE, UPLOAD_FOLDER, ALLOWED_EXTENSIONS, MUTAGEN_AVAILABLE,
    get_current_user, verify_telegram_webapp_data, allowed_file,
    login_required, admin_required
)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DB_FILE'] = DB_FILE
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# ============================================================================
# DATABASE INITIALIZATION (unchanged)
# ============================================================================

def ensure_valid_db():
    # ... (same as before) ...

def init_db():
    # ... (same as before) ...

init_db()

# ============================================================================
# ROUTES (keep all your routes exactly as they are)
# ============================================================================

# ... your existing routes (@app.route) ...

# ============================================================================
# REGISTER BLUEPRINTS (unchanged)
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

# ... rest (socketio events, if __name__ == '__main__') ...
# Import shared utilities from common.py to avoid circular imports
from common import DB_FILE, get_current_user, verify_telegram_webapp_data

# Configuration
UPLOAD_FOLDER = 'uploads'
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
# DATABASE INITIALIZATION WITH AUTO-HEAL
# ============================================================================

def ensure_valid_db():
    """Delete corrupt SQLite file if it exists but is not a valid database."""
    if not os.path.exists(DB_FILE):
        return
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master LIMIT 1")
        c.fetchone()
        conn.close()
    except sqlite3.DatabaseError:
        print(f"⚠️ Corrupt database '{DB_FILE}' detected. Deleting...")
        os.remove(DB_FILE)
        print("✅ Removed. Fresh database will be created.")
    except Exception as e:
        print(f"⚠️ Unexpected error while checking DB: {e}")

def init_db():
    """Initialize database with all required tables (auto-heals corrupt DB)."""
    ensure_valid_db()

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

# Initialize database on startup
init_db()

# ============================================================================
# UTILITY FUNCTIONS (now imported from common.py)
# ============================================================================

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
# MAIN ROUTES (unchanged)
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

# ... (keep all other routes exactly as they were) ...

# ============================================================================
# REGISTER BLUEPRINTS (unchanged)
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
# SOCKET.IO EVENTS (unchanged)
# ============================================================================

# ... (keep everything below as is) ...

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.environ.get('PORT', 5024))
    host = os.environ.get('HOST', '127.0.0.1')
    socketio.run(app, debug=debug_mode, port=port, host=host)