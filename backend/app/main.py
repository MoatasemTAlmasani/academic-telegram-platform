from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from backend.app.api.router import api_router
from backend.app.api.routes.health import router as health_router
from backend.app.core.config import get_settings
from backend.app.core.errors import register_exception_handlers
from backend.app.core.logging import configure_logging
from backend.app.core.static_files import PublicStaticFiles
from database.session import engine


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    try:
        yield
    finally:
        await engine.dispose()


settings = get_settings()

app = FastAPI(
    title="Academic Services Platform API",
    description="Foundation API for the Telegram-based academic and student services platform.",
    version="0.1.0",
    lifespan=lifespan,
)


STATIC_ROOT = Path(__file__).resolve().parent / "static"

app.mount(
    "/miniapp/static",
    PublicStaticFiles(directory=STATIC_ROOT / "miniapp"),
    name="miniapp-static",
)


@app.get("/miniapp", include_in_schema=False)
async def miniapp_home():
    return FileResponse(STATIC_ROOT / "miniapp" / "index.html")


app.mount(
    "/admin/static",
    PublicStaticFiles(directory=STATIC_ROOT / "admin"),
    name="admin-static",
)


@app.get("/admin", include_in_schema=False)
async def admin_dashboard():
    return FileResponse(STATIC_ROOT / "admin" / "index.html")


register_exception_handlers(app)

# Keep simple root health paths for operational probes and existing clients.
app.include_router(health_router)
app.include_router(api_router)
