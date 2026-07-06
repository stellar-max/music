# bot_services/auth_service.py - Authentication service

import sqlite3
import uuid
from datetime import datetime, timedelta
from bot_config import config, logger

def create_user(telegram_id: int, username: str, first_name: str, last_name: str = ''):
    """Create a new user in database"""
    display_name = first_name
    if last_name:
        display_name += f" {last_name}"
    nickname = username if username else f"user_{telegram_id}"
    
    conn = sqlite3.connect(config.DB_FILE)
    c = conn.cursor()
    try:
        c.execute(
            """INSERT INTO users (telegram_id, username, first_name, last_name, display_name, nickname)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (telegram_id, username, first_name, last_name, display_name, nickname)
        )
        conn.commit()
        user_id = c.lastrowid
        logger.info(f"Created user: {display_name} ({telegram_id})")
        return user_id
    except sqlite3.IntegrityError as e:
        logger.error(f"Error creating user: {e}")
        return None
    finally:
        conn.close()

def get_user_by_telegram_id(telegram_id: int):
    """Get user from database by Telegram ID"""
    conn = sqlite3.connect(config.DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    user = c.fetchone()
    conn.close()
    return dict(user) if user else None

def create_auth_token(telegram_id: int) -> str:
    """Create a short-lived authentication token"""
    token = str(uuid.uuid4()).replace('-', '')[:32]
    expires_at = datetime.now() + timedelta(minutes=10)
    
    conn = sqlite3.connect(config.DB_FILE)
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO auth_tokens (token, telegram_id, expires_at) VALUES (?, ?, ?)",
            (token, telegram_id, expires_at.isoformat())
        )
        conn.commit()
        logger.info(f"Created auth token for user {telegram_id}")
        return token
    except sqlite3.IntegrityError as e:
        logger.error(f"Error creating auth token: {e}")
        return None
    finally:
        conn.close()

def verify_auth_token(token: str):
    """Verify an authentication token"""
    conn = sqlite3.connect(config.DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(
        "SELECT telegram_id FROM auth_tokens WHERE token = ? AND expires_at > datetime('now')",
        (token,)
    )
    result = c.fetchone()
    conn.close()
    return dict(result) if result else None
