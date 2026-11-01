"""PostgreSQL advisory lock preventing competing Telegram pollers."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

_TELEGRAM_WORKER_LOCK_ID = 7_414_002_026


class TelegramWorkerLock:
    """Hold a session-level PostgreSQL lock for the worker lifetime."""

    def __init__(self, engine: AsyncEngine) -> None:
        self.engine = engine
        self.connection: AsyncConnection | None = None

    async def acquire(self) -> bool:
        if self.connection is not None:
            return True

        connection = await self.engine.connect()
        try:
            result = await connection.execute(
                text("SELECT pg_try_advisory_lock(:lock_id)"),
                {"lock_id": _TELEGRAM_WORKER_LOCK_ID},
            )
            acquired = bool(result.scalar())
            await connection.commit()
            if acquired:
                self.connection = connection
                return True
        except Exception:
            await connection.close()
            raise

        await connection.close()
        return False

    async def release(self) -> None:
        connection, self.connection = self.connection, None
        if connection is None:
            return
        try:
            await connection.execute(
                text("SELECT pg_advisory_unlock(:lock_id)"),
                {"lock_id": _TELEGRAM_WORKER_LOCK_ID},
            )
            await connection.commit()
        finally:
            await connection.close()
