# routes/auth.py
# Authentication routes - Login, Logout, Telegram auth

import sqlite3
import json
from flask import Blueprint, request, jsonify, session, redirect, render_template
from functools import wraps
from common import get_current_user, verify_telegram_webapp_data, DB_FILE

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/telegram', methods=['POST'])
def auth_telegram():
    """Authenticate via Telegram Web App data"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        init_data = data.get('initData', '')
        if not init_data:
            return jsonify({'error': 'No initData provided'}), 400
        
        user_data = verify_telegram_webapp_data(init_data)
        if not user_data:
            return jsonify({'error': 'Invalid Telegram data hash'}), 401
        
        telegram_id = user_data.get('id')
        username = user_data.get('username', '')
        first_name = user_data.get('first_name', '')
        last_name = user_data.get('last_name', '')
        avatar_url = user_data.get('photo_url')
        
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Check for existing user
        c.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        user = c.fetchone()
        
        if user:
            # Update existing user
            current_nickname = user['nickname'] if user['nickname'] else ''
            if not current_nickname and username:
                current_nickname = username
            
            c.execute("""UPDATE users 
                         SET username = ?, first_name = ?, last_name = ?, avatar_url = ?, nickname = ?
                         WHERE telegram_id = ?""",
                      (username, first_name, last_name, avatar_url, current_nickname, telegram_id))
            user_id = user['id']
        else:
            # Create new user
            display_name = first_name
            if last_name:
                display_name += f" {last_name}"
            
            nickname = username if username else None
            
            c.execute("""INSERT INTO users (telegram_id, username, first_name, last_name, avatar_url, display_name, nickname)
                         VALUES (?, ?, ?, ?, ?, ?, ?)""",
                      (telegram_id, username, first_name, last_name, avatar_url, display_name, nickname))
            user_id = c.lastrowid
        
        conn.commit()
        
        # Get updated user data
        c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = dict(c.fetchone())
        conn.close()
        
        # Save to session
        session['user_id'] = user_id
        session['telegram_id'] = telegram_id
        
        return jsonify({'success': True, 'user': user})
    except Exception as e:
        print(f"Auth error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout user"""
    session.clear()
    return jsonify({'success': True})

@auth_bp.route('/browser/<token>')
def auth_browser(token):
    """Authenticate browser session via token from Telegram bot"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Check token validity (10 minute expiry)
    c.execute("SELECT telegram_id FROM auth_tokens WHERE token = ? AND expires_at > datetime('now')", (token,))
    row = c.fetchone()
    
    if not row:
        conn.close()
        return "Link expired or invalid. Request a new one from the bot with /login", 400
        
    telegram_id = row[0]
    
    # Find user
    c.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    user = c.fetchone()
    
    if not user:
        conn.close()
        return "User not found. Please login via Telegram Web App first.", 404
        
    # Authenticate
    session['user_id'] = user['id']
    session['telegram_id'] = telegram_id
    
    # Delete used token
    c.execute("DELETE FROM auth_tokens WHERE token = ?", (token,))
    conn.commit()
    conn.close()
    
    return redirect('/app')

@auth_bp.route('/profile', methods=['GET'])
def get_profile():
    """Get current user profile"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(user)
