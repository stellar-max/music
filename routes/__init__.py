# routes/__init__.py
# Routes blueprint initialization

from routes.auth import auth_bp
from routes.tracks import tracks_bp
from routes.albums import albums_bp
from routes.admin import admin_bp
from routes.rooms import rooms_bp

__all__ = [
    'auth_bp',
    'tracks_bp', 
    'albums_bp',
    'admin_bp',
    'rooms_bp'
]
