"""Provides shared configuration, authentication helpers, upload validation, and Telegram Web App verification."""

import hashlib
import hmac
import json
import os
import sqlite3
from functools import wraps
from urllib.parse import parse_qsl

from flask import jsonify, redirect, session


DB_FILE = os.environ.get("DB_FILE", "music.db")
UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")
TELEGRAM_BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

ALLOWED_EXTENSIONS = {
    "mp3",
    "wav",
    "ogg",
    "m4a",
    "flac",
    "aac",
    "jpg",
    "jpeg",
    "png",
    "webp",
}


try:
    from mutagen.mp3 import MP3
    from mutagen.id3 import APIC, ID3, ID3NoHeaderError, TIT2, TPE1

    MUTAGEN_AVAILABLE = True
except ImportError:
    MP3 = None
    APIC = None
    ID3 = None
    ID3NoHeaderError = None
    TIT2 = None
    TPE1 = None
    MUTAGEN_AVAILABLE = False


def get_db_connection():
    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def get_current_user():
    user_id = session.get("user_id")

    if not user_id:
        return None

    connection = get_db_connection()

    try:
        user = connection.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

        return dict(user) if user else None

    except sqlite3.Error as error:
        print(f"Failed to get current user: {error}")
        return None

    finally:
        connection.close()


def allowed_file(filename):
    if not filename or "." not in filename:
        return False

    extension = filename.rsplit(".", 1)[1].lower()
    return extension in ALLOWED_EXTENSIONS


def login_required(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify(
                {
                    "error": "Unauthorized",
                    "message": "Login required",
                }
            ), 401

        return function(*args, **kwargs)

    return decorated_function


def admin_required(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        if not session.get("admin"):
            return redirect("/admin/login")

        return function(*args, **kwargs)

    return decorated_function


def verify_telegram_webapp_data(init_data):
    if not init_data or not TELEGRAM_BOT_TOKEN:
        return None

    try:
        parsed_data = dict(
            parse_qsl(
                init_data,
                keep_blank_values=True,
            )
        )

        received_hash = parsed_data.pop("hash", None)

        if not received_hash:
            return None

        data_check_string = "\n".join(
            f"{key}={value}"
            for key, value in sorted(parsed_data.items())
        )

        secret_key = hmac.new(
            key=b"WebAppData",
            msg=TELEGRAM_BOT_TOKEN.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()

        calculated_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(
            calculated_hash,
            received_hash,
        ):
            return None

        user_data = parsed_data.get("user")

        if not user_data:
            return None

        return json.loads(user_data)

    except (
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ) as error:
        print(f"Invalid Telegram Web App data: {error}")
        return None

    except Exception as error:
        print(f"Telegram verification failed: {error}")
        return None
