# common.py - Shared utilities and constants

import os
import sqlite3
import hmac
import hashlib
import json
from flask import session
from werkzeug.security import generate_password_hash, check_password_hash

# Database file path
DB_FILE = 'music.db'

# Telegram bot token (used in verify_telegram_webapp_data)
TELEGRAM_BOT_TOKEN = os.environ.get('BOT_TOKEN', '')

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