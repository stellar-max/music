"""Runs the Flask music app, initializes SQLite, registers API blueprints, and serves Socket.IO."""

import os
import sqlite3

from flask import Flask, render_template, request
from flask_socketio import SocketIO
from werkzeug.security import generate_password_hash

from common import DB_FILE, UPLOAD_FOLDER, get_current_user


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "your-secret-key-change-in-production",
)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["DB_FILE"] = DB_FILE

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db_directory = os.path.dirname(os.path.abspath(DB_FILE))
os.makedirs(db_directory, exist_ok=True)

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading",
)


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    avatar_url TEXT,
    nickname TEXT UNIQUE,
    display_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS albums (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS album_likes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    album_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (album_id) REFERENCES albums(id),
    UNIQUE (user_id, album_id)
);

CREATE TABLE IF NOT EXISTS album_tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    album_id INTEGER,
    track_id INTEGER,
    sort_order INTEGER DEFAULT 0,
    FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE,
    FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE,
    UNIQUE (album_id, track_id)
);

CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password_hash TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS auth_tokens (
    token TEXT PRIMARY KEY,
    telegram_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS likes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    track_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (track_id) REFERENCES tracks(id),
    UNIQUE (user_id, track_id)
);

CREATE TABLE IF NOT EXISTS track_plays (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    track_id INTEGER,
    play_count INTEGER DEFAULT 1,
    last_played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (track_id) REFERENCES tracks(id),
    UNIQUE (user_id, track_id)
);

CREATE TABLE IF NOT EXISTS rooms (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    host_id INTEGER NOT NULL,
    current_track_id INTEGER,
    is_playing INTEGER DEFAULT 0,
    current_time REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (host_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS room_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id TEXT,
    user_id INTEGER,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE (room_id, user_id)
);

CREATE TABLE IF NOT EXISTS room_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id TEXT,
    track_id INTEGER,
    added_by_id INTEGER,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
    FOREIGN KEY (track_id) REFERENCES tracks(id),
    FOREIGN KEY (added_by_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_tracks_user_id
ON tracks(user_id);

CREATE INDEX IF NOT EXISTS idx_tracks_slug
ON tracks(slug);

CREATE INDEX IF NOT EXISTS idx_albums_user_id
ON albums(user_id);

CREATE INDEX IF NOT EXISTS idx_albums_slug
ON albums(slug);

CREATE INDEX IF NOT EXISTS idx_users_telegram_id
ON users(telegram_id);

CREATE INDEX IF NOT EXISTS idx_users_nickname
ON users(nickname);

CREATE INDEX IF NOT EXISTS idx_room_members_room
ON room_members(room_id);

CREATE INDEX IF NOT EXISTS idx_room_queue_room
ON room_queue(room_id);
"""


def ensure_valid_db():
    if not os.path.exists(DB_FILE):
        return

    connection = None

    try:
        connection = sqlite3.connect(DB_FILE)
        result = connection.execute("PRAGMA integrity_check").fetchone()

        if not result or result[0] != "ok":
            raise sqlite3.DatabaseError("SQLite integrity check failed")

    except sqlite3.DatabaseError:
        if connection is not None:
            connection.close()
            connection = None

        os.remove(DB_FILE)
        print(f"Corrupt database removed: {DB_FILE}")

    finally:
        if connection is not None:
            connection.close()


def init_db():
    ensure_valid_db()

    connection = sqlite3.connect(DB_FILE)

    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(SCHEMA)

        admin_exists = connection.execute(
            "SELECT 1 FROM admins LIMIT 1"
        ).fetchone()

        if admin_exists is None:
            username = os.environ.get("ADMIN_USERNAME", "admin")
            password = os.environ.get("ADMIN_PASSWORD", "admin123")

            connection.execute(
                """
                INSERT INTO admins (
                    username,
                    password_hash
                )
                VALUES (?, ?)
                """,
                (
                    username,
                    generate_password_hash(password),
                ),
            )

        connection.commit()
        print("Database initialized successfully.")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


init_db()


@app.route("/")
def index():
    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row

    try:
        cursor = connection.cursor()
        search_query = request.args.get("q", "").strip()
        current_user = get_current_user()

        tracks_query = """
            SELECT
                t.*,
                u.nickname,
                u.display_name,
                u.avatar_url,
                COALESCE(t.plays_count, 0) AS plays_count,
                COALESCE(t.likes_count, 0) AS likes_count
            FROM tracks AS t
            JOIN users AS u
                ON t.user_id = u.id
            WHERE t.hidden = 0
        """

        tracks_params = []

        if search_query:
            tracks_query += """
                AND (
                    t.title LIKE ?
                    OR t.artist LIKE ?
                )
            """

            search_term = f"%{search_query}%"
            tracks_params.extend(
                (
                    search_term,
                    search_term,
                )
            )

        tracks_query += """
            ORDER BY
                t.is_pinned DESC,
                t.created_at DESC
            LIMIT 50
        """

        cursor.execute(
            tracks_query,
            tracks_params,
        )

        tracks = []

        for row in cursor.fetchall():
            track = dict(row)

            if current_user:
                track["is_liked"] = cursor.execute(
                    """
                    SELECT 1
                    FROM likes
                    WHERE user_id = ?
                      AND track_id = ?
                    LIMIT 1
                    """,
                    (
                        current_user["id"],
                        track["id"],
                    ),
                ).fetchone() is not None
            else:
                track["is_liked"] = False

            tracks.append(track)

        albums_query = """
            SELECT
                a.*,
                u.nickname,
                u.display_name,
                u.avatar_url,
                COALESCE(a.plays_count, 0) AS plays_count,
                COALESCE(a.likes_count, 0) AS likes_count
            FROM albums AS a
            JOIN users AS u
                ON a.user_id = u.id
            WHERE a.hidden = 0
        """

        albums_params = []

        if search_query:
            albums_query += """
                AND (
                    a.title LIKE ?
                    OR a.description LIKE ?
                )
            """

            search_term = f"%{search_query}%"
            albums_params.extend(
                (
                    search_term,
                    search_term,
                )
            )

        albums_query += """
            ORDER BY
                a.is_pinned DESC,
                a.created_at DESC
            LIMIT 50
        """

        cursor.execute(
            albums_query,
            albums_params,
        )

        albums = []

        for row in cursor.fetchall():
            album = dict(row)

            if current_user:
                album["is_liked"] = cursor.execute(
                    """
                    SELECT 1
                    FROM album_likes
                    WHERE user_id = ?
                      AND album_id = ?
                    LIMIT 1
                    """,
                    (
                        current_user["id"],
                        album["id"],
                    ),
                ).fetchone() is not None
            else:
                album["is_liked"] = False

            albums.append(album)

        return render_template(
            "unified.html",
            tracks=tracks,
            albums=albums,
            current_user=current_user,
            search_query=search_query,
            mode="library",
        )

    finally:
        connection.close()


from routes.auth import auth_bp
from routes.tracks import tracks_bp
from routes.albums import albums_bp
from routes.admin import admin_bp
from routes.rooms import rooms_bp


app.register_blueprint(
    auth_bp,
    url_prefix="/api/auth",
)

app.register_blueprint(
    tracks_bp,
    url_prefix="/api/tracks",
)

app.register_blueprint(
    albums_bp,
    url_prefix="/api/albums",
)

app.register_blueprint(
    admin_bp,
    url_prefix="/admin/api",
)

app.register_blueprint(
    rooms_bp,
    url_prefix="/api/rooms",
)


if __name__ == "__main__":
    socketio.run(
        app,
        debug=os.environ.get(
            "FLASK_DEBUG",
            "false",
        ).lower() == "true",
        host=os.environ.get(
            "HOST",
            "0.0.0.0",
        ),
        port=int(
            os.environ.get(
                "PORT",
                "5024",
            )
        ),
    )
