# bot_config.py - Telegram Bot Configuration

import os
import logging
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

@dataclass
class BotConfig:
    """Bot configuration settings"""
    BOT_TOKEN: str = os.environ.get('BOT_TOKEN', '')
    WEBAPP_URL: str = os.environ.get('WEBAPP_URL', 'http://localhost:5024')
    DB_FILE: str = 'music.db'
    
    # Bot messages
    WELCOME_TEXT: str = """
🎵 **Welcome to SimpleWebPlayer, {first_name}!**

Your personal music streaming hub with:
• 🎤 **Synced LRC Lyrics**
• 📀 **Album & Playlist Management**
• 👥 **Collaborative Rooms**
• 📱 **Telegram Integration**

🔑 **Click below to open the web player and start listening!**
    """
    
    HELP_TEXT: str = """
🤖 **SimpleWebPlayer Bot Help**

**Commands:**
• `/start` - Welcome and login
• `/login` - Get web player login link
• `/play <song>` - Play a song on your web player
• `/room` - Manage collaborative rooms
• `/help` - Show this help

**Features:**
• 🎵 **Web Player** - Stream your music with synced lyrics
• 👥 **Rooms** - Listen together with friends in real-time
• 📱 **Telegram Integration** - Control playback from your phone

🔗 **Web Player:** {WEBAPP_URL}
    """
    
    PLAY_USAGE: str = """
🎵 **Usage:** `/play <song name>`

**Example:** `/play Bohemian Rhapsody`

You can also search by artist:
• `/play Queen Bohemian Rhapsody`
• `/play artist:Lady Gaga`
    """
    
    ROOM_TEXT: str = """
🎧 **Room Management**

Create or join collaborative listening rooms to enjoy music together!

• 📋 **List Rooms** - See all active rooms
• ➕ **Create Room** - Create a new room
• 🔗 **Join Room** - Join an existing room
    """

config = BotConfig()
