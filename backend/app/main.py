from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.api.router import api_router
from backend.app.core.config import get_settings
from backend.app.core.errors import register_exception_handlers
from backend.app.core.logging import configure_logging
from backend.app.infrastructure.telegram.bot_runner import TelegramBotRunner


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    configure_logging()

    telegram_runner = None

    if settings.telegram_bot_token:
        telegram_runner = TelegramBotRunner(
            settings.telegram_bot_token
        )
        await telegram_runner.start()

    try:
        yield
    finally:
        if telegram_runner:
            await telegram_runner.stop()


settings = get_settings()

app = FastAPI(
    title="Academic Services Platform API",
    description="Foundation API for the Telegram-based academic and student services platform.",
    version="0.1.0",
    lifespan=lifespan,
)


app.mount(
    "/miniapp/static",
    StaticFiles(directory="backend/app/static/miniapp"),
    name="miniapp-static",
)


@app.get("/miniapp", include_in_schema=False)
async def miniapp_home():
    return FileResponse("backend/app/static/miniapp/index.html")


app.mount(
    "/admin/static",
    StaticFiles(directory="backend/app/static/admin"),
    name="admin-static",
)


@app.get("/admin", include_in_schema=False)
async def admin_dashboard():
    return FileResponse("backend/app/static/admin/index.html")


register_exception_handlers(app)

app.include_router(api_router)
