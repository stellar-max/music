"""Runs the Telegram bot inside the Flask worker using a background thread."""

import asyncio
import threading
from typing import Optional

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
)

from bot_config import config, logger
from bot_handlers import (
    button_callback,
    help_command,
    login_command,
    play_command,
    room_command,
    start_command,
)
from bot_handlers.play import init_socketio


_bot_thread: Optional[threading.Thread] = None
_bot_thread_lock = threading.Lock()


async def load_bot_identity(application: Application) -> None:
    bot_user = await application.bot.get_me()

    config.set_bot_identity(
        name=bot_user.first_name or "Music Player",
        username=bot_user.username or "",
    )

    logger.info(
        "Connected to Telegram as %s (@%s)",
        config.BOT_NAME,
        config.BOT_USERNAME or "unknown",
    )


def build_bot(socketio_instance=None) -> Application:
    if not config.BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN environment variable is missing"
        )

    init_socketio(socketio_instance)

    application = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .post_init(load_bot_identity)
        .build()
    )

    application.add_handler(
        CommandHandler(
            "start",
            start_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "login",
            login_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "play",
            play_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "room",
            room_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "help",
            help_command,
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            button_callback,
        )
    )

    return application


def run_bot(socketio_instance=None) -> None:
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)

    try:
        application = build_bot(socketio_instance)

        logger.info(
            "Starting Telegram bot polling"
        )

        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            stop_signals=None,
            close_loop=False,
        )

    except Exception:
        logger.exception(
            "Telegram bot stopped with an error"
        )

    finally:
        asyncio.set_event_loop(None)

        if not event_loop.is_closed():
            event_loop.close()

        logger.info(
            "Telegram bot polling stopped"
        )


def start_bot_background(
    socketio_instance=None,
) -> threading.Thread:
    global _bot_thread

    with _bot_thread_lock:
        if (
            _bot_thread is not None
            and _bot_thread.is_alive()
        ):
            logger.info(
                "Telegram bot thread is already running"
            )
            return _bot_thread

        _bot_thread = threading.Thread(
            target=run_bot,
            args=(socketio_instance,),
            name="telegram-bot",
            daemon=True,
        )

        _bot_thread.start()

        logger.info(
            "Telegram bot background thread started"
        )

        return _bot_thread


if __name__ == "__main__":
    run_bot()
