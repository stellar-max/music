"""Runs the Telegram bot inside the Flask web worker using a background thread."""

import asyncio
import threading

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


_bot_thread = None
_bot_thread_lock = threading.Lock()


def build_bot(socketio_instance):
    if not config.BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is missing")

    init_socketio(socketio_instance)

    application = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start_command)
    )
    application.add_handler(
        CommandHandler("login", login_command)
    )
    application.add_handler(
        CommandHandler("play", play_command)
    )
    application.add_handler(
        CommandHandler("room", room_command)
    )
    application.add_handler(
        CommandHandler("help", help_command)
    )
    application.add_handler(
        CallbackQueryHandler(button_callback)
    )

    return application


def run_bot(socketio_instance=None):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        application = build_bot(socketio_instance)

        logger.info("Telegram bot polling started")

        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            stop_signals=None,
            close_loop=True,
        )

    except Exception:
        logger.exception("Telegram bot stopped with an error")

    finally:
        asyncio.set_event_loop(None)

        if not loop.is_closed():
            loop.close()


def start_bot_background(socketio_instance=None):
    global _bot_thread

    with _bot_thread_lock:
        if _bot_thread and _bot_thread.is_alive():
            return _bot_thread

        _bot_thread = threading.Thread(
            target=run_bot,
            args=(socketio_instance,),
            name="telegram-bot",
            daemon=True,
        )

        _bot_thread.start()
        logger.info("Telegram bot background thread started")

        return _bot_thread


if __name__ == "__main__":
    run_bot()
