"""Dedicated process entry point for the single Telegram polling worker."""

from __future__ import annotations

import asyncio
import signal

from backend.app.core.config import get_settings
from backend.app.core.logging import configure_logging
from backend.app.infrastructure.telegram.bot_runner import TelegramBotRunner
from backend.app.infrastructure.telegram.worker_lock import TelegramWorkerLock
from database.session import engine


async def run_worker() -> None:
    configure_logging()
    settings = get_settings()
    if settings.telegram_mode != "polling":
        raise RuntimeError("Set TELEGRAM_MODE=polling to enable the dedicated polling worker.")
    if settings.telegram_bot_token is None:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is required for the bot worker.")

    lock = TelegramWorkerLock(engine)
    if not await lock.acquire():
        raise RuntimeError("A Telegram polling worker already holds the database lock.")

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for handled_signal in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(handled_signal, stop_event.set)

    runner = TelegramBotRunner(settings.telegram_bot_token)
    try:
        await runner.start()
        worker_task = runner._task
        stop_task = asyncio.create_task(stop_event.wait())
        done, _ = await asyncio.wait(
            {worker_task, stop_task},
            return_when=asyncio.FIRST_COMPLETED,
        )
        if worker_task in done:
            await worker_task
    finally:
        if "stop_task" in locals():
            stop_task.cancel()
        await runner.stop()
        await lock.release()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_worker())
