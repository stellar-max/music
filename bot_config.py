"""Stores Telegram bot settings, runtime identity, and reusable messages."""

import logging
import os
from dataclasses import dataclass, field


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


@dataclass
class BotConfig:
    BOT_TOKEN: str = field(
        default_factory=lambda: os.environ.get("BOT_TOKEN", "")
    )

    WEBAPP_URL: str = field(
        default_factory=lambda: os.environ.get(
            "WEBAPP_URL",
            "http://localhost:5024",
        ).rstrip("/")
    )

    DB_FILE: str = field(
        default_factory=lambda: os.environ.get(
            "DB_FILE",
            "music.db",
        )
    )

    BOT_NAME: str = "Music Player"
    BOT_USERNAME: str = ""

    WELCOME_TEXT: str = """
🎵 **Welcome to {bot_name}, {first_name}!**

Your personal music streaming hub with:
• 🎤 **Synced LRC Lyrics**
• 📀 **Album & Playlist Management**
• 👥 **Collaborative Rooms**
• 📱 **Telegram Integration**

🔑 **Open the player below to start listening.**
""".strip()

    HELP_TEXT: str = """
🤖 **{bot_name} Help**

**Commands:**
• `/start` — Open the player
• `/login` — Generate a login link
• `/play <song>` — Search or play a track
• `/room` — Manage listening rooms
• `/help` — Show this message

🔗 **Web Player:** {webapp_url}
""".strip()

    PLAY_USAGE: str = """
🎵 **Usage:** `/play <song name>`

**Examples:**
• `/play Bohemian Rhapsody`
• `/play Queen Bohemian Rhapsody`
""".strip()

    ROOM_TEXT: str = """
🎧 **Room Management**

Create or join collaborative listening rooms.

• 📋 **List Rooms**
• ➕ **Create Room**
• 🔗 **Join Room**
""".strip()

    def set_bot_identity(
        self,
        name: str,
        username: str,
    ) -> None:
        self.BOT_NAME = name or "Music Player"
        self.BOT_USERNAME = (username or "").lstrip("@")

        logger.info(
            "Bot identity loaded: %s (@%s)",
            self.BOT_NAME,
            self.BOT_USERNAME or "unknown",
        )

    @property
    def mini_app_url(self) -> str:
        if not self.BOT_USERNAME:
            return ""

        return f"https://t.me/{self.BOT_USERNAME}?startapp"

    def mini_app_deep_link(
        self,
        start_param: str = "",
    ) -> str:
        if not self.BOT_USERNAME:
            return self.WEBAPP_URL

        link = f"https://t.me/{self.BOT_USERNAME}?startapp"

        if start_param:
            link += f"={start_param}"

        return link


config = BotConfig()
