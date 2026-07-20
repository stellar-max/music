"""Runs the Flask music app, initializes SQLite, registers APIs, and starts the Telegram bot."""

import os
import sqlite3

from flask import Flask, redirect, render_template, request, url_for
from flask_socketio import SocketIO
from werkzeug.security import generate_password_hash

from common import DB_FILE, get_current_user


UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")

app = Flask(__name__)

app.config.update(
    SECRET_KEY=os.environ.get(
        "SECRET_KEY",
        "your-secret-key-change-in-production",
    ),
    UPLOAD_FOLDER=UPLOAD_FOLDER,
    DB_FILE=DB_FILE,
    MAX_CONTENT_LENGTH=100 * 1024 * 1024,
)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

database_directory = os.path.dirname(
    os.path.abspath(DB_FILE)
)
os.makedirs(database_directory, exist_ok=True)

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
    FOREIGN KEY (album_id)
        REFERENCES albums(id)
        ON DELETE CASCADE,
    FOREIGN KEY (track_id)
        REFERENCES tracks(id)
        ON DELETE CASCADE,
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
    FOREIGN KEY (host_id) REFERENCES users(id),
    FOREIGN KEY (current_track_id) REFERENCES tracks(id)
);

CREATE TABLE IF NOT EXISTS room_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id TEXT,
    user_id INTEGER,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id)
        REFERENCES rooms(id)
        ON DELETE CASCADE,
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
    FOREIGN KEY (room_id)
        REFERENCES rooms(id)
        ON DELETE CASCADE,
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

CREATE INDEX IF NOT EXISTS idx_auth_tokens_expiry
ON auth_tokens(expires_at);
"""


def get_database_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(
        DB_FILE,
        timeout=30,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 30000")
    return connection


def ensure_valid_db() -> None:
    if not os.path.exists(DB_FILE):
        return

    connection = None

    try:
        connection = sqlite3.connect(
            DB_FILE,
            timeout=30,
        )

        result = connection.execute(
            "PRAGMA integrity_check"
        ).fetchone()

        if not result or result[0] != "ok":
            raise sqlite3.DatabaseError(
                "SQLite integrity check failed"
            )

    except sqlite3.DatabaseError:
        if connection is not None:
            connection.close()
            connection = None

        os.remove(DB_FILE)

        print(
            f"Corrupt database removed: {DB_FILE}",
            flush=True,
        )

    finally:
        if connection is not None:
            connection.close()


def init_db() -> None:
    ensure_valid_db()

    connection = get_database_connection()

    try:
        connection.executescript(SCHEMA)

        admin_exists = connection.execute(
            """
            SELECT 1
            FROM admins
            LIMIT 1
            """
        ).fetchone()

        if admin_exists is None:
            admin_username = os.environ.get(
                "ADMIN_USERNAME",
                "admin",
            )

            admin_password = os.environ.get(
                "ADMIN_PASSWORD",
                "admin123",
            )

            connection.execute(
                """
                INSERT INTO admins (
                    username,
                    password_hash
                )
                VALUES (?, ?)
                """,
                (
                    admin_username,
                    generate_password_hash(
                        admin_password
                    ),
                ),
            )

        connection.execute(
            """
            DELETE FROM auth_tokens
            WHERE expires_at <= CURRENT_TIMESTAMP
            """
        )

        connection.commit()

        print(
            "Database initialized successfully.",
            flush=True,
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


init_db()


def load_library():
    connection = get_database_connection()

    try:
        cursor = connection.cursor()

        search_query = request.args.get(
            "q",
            "",
        ).strip()

        current_user = get_current_user()

        tracks_query = """
            SELECT
                t.*,
                u.nickname,
                u.display_name,
                u.avatar_url,
                COALESCE(t.plays_count, 0)
                    AS plays_count,
                COALESCE(t.likes_count, 0)
                    AS likes_count
            FROM tracks AS t
            JOIN users AS u
                ON u.id = t.user_id
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

        tracks_rows = cursor.execute(
            tracks_query,
            tracks_params,
        ).fetchall()

        tracks = []

        for row in tracks_rows:
            track = dict(row)

            if current_user:
                liked = cursor.execute(
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
                ).fetchone()

                track["is_liked"] = liked is not None

            else:
                track["is_liked"] = False

            tracks.append(track)

        albums_query = """
            SELECT
                a.*,
                u.nickname,
                u.display_name,
                u.avatar_url,
                COALESCE(a.plays_count, 0)
                    AS plays_count,
                COALESCE(a.likes_count, 0)
                    AS likes_count
            FROM albums AS a
            JOIN users AS u
                ON u.id = a.user_id
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

        albums_rows = cursor.execute(
            albums_query,
            albums_params,
        ).fetchall()

        albums = []

        for row in albums_rows:
            album = dict(row)

            if current_user:
                liked = cursor.execute(
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
                ).fetchone()

                album["is_liked"] = liked is not None

            else:
                album["is_liked"] = False

            albums.append(album)

        return {
            "tracks": tracks,
            "albums": albums,
            "current_user": current_user,
            "search_query": search_query,
        }

    finally:
        connection.close()


@app.route("/")
def index():
    library = load_library()

    requested_view = request.args.get(
        "view",
        "library",
    ).strip()

    return render_template(
        "unified.html",
        tracks=library["tracks"],
        albums=library["albums"],
        current_user=library["current_user"],
        search_query=library["search_query"],
        mode=requested_view,
    )


@app.route("/app")
def app_alias():
    return redirect(
        url_for("index")
    )


@app.route("/rooms")
def rooms_alias():
    return redirect(
        url_for(
            "index",
            view="rooms",
        )
    )


@app.route("/room/<string:room_id>")
def room_alias(room_id):
    return redirect(
        url_for(
            "index",
            view="room",
            room_id=room_id,
        )
    )


@app.route("/user/<string:nickname>")
def user_library_alias(nickname):
    return redirect(
        url_for(
            "index",
            view="library",
            user=nickname,
        )
    )


@app.route("/health")
def health():
    return {
        "status": "ok",
        "database": os.path.exists(DB_FILE),
        "bot_enabled": bool(
            os.environ.get("BOT_TOKEN")
        ),
    }, 200


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


bot_thread = None


def start_integrated_bot() -> None:
    global bot_thread

    bot_token = os.environ.get(
        "BOT_TOKEN",
        "",
    ).strip()

    if not bot_token:
        print(
            "BOT_TOKEN is missing. "
            "Web app will run without Telegram bot.",
            flush=True,
        )
        return

    try:
        from bot import start_bot_background

        bot_thread = start_bot_background(
            socketio
        )

        print(
            "Telegram bot started inside "
            "the web worker process.",
            flush=True,
        )

    except Exception as error:
        print(
            f"Failed to start Telegram bot: {error}",
            flush=True,
        )


start_integrated_bot()


if __name__ == "__main__":
    debug_mode = os.environ.get(
        "FLASK_DEBUG",
        "false",
    ).lower() == "true"

    host = os.environ.get(
        "HOST",
        "0.0.0.0",
    )

    port = int(
        os.environ.get(
            "PORT",
            "5024",
        )
    )

    socketio.run(
        app,
        debug=debug_mode,
        host=host,
        port=port,
        allow_unsafe_werkzeug=True,
        )
