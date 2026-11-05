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


# Public EHTERAF website routes. Keep these after API routers so API paths
# retain their existing precedence.
WEBSITE_ROOT = STATIC_ROOT / "website"

app.mount(
    "/website/static",
    PublicStaticFiles(directory=WEBSITE_ROOT),
    name="website-static",
)


@app.get("/", include_in_schema=False)
async def public_website_home():
    return FileResponse(WEBSITE_ROOT / "index.html")


@app.get("/login", include_in_schema=False)
async def public_login():
    return FileResponse(WEBSITE_ROOT / "login.html")


@app.get("/profile", include_in_schema=False)
async def public_profile():
    return FileResponse(WEBSITE_ROOT / "profile.html")


@app.get("/offline", include_in_schema=False)
async def public_offline():
    return FileResponse(WEBSITE_ROOT / "offline.html")


@app.get("/service-worker.js", include_in_schema=False)
async def public_service_worker():
    return FileResponse(
        WEBSITE_ROOT / "sw.js",
        media_type="application/javascript",
        headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"},
    )


@app.get("/{page_name}", include_in_schema=False)
async def public_website_page(page_name: str):
    public_pages = {
        "about",
        "academic-services",
        "technical-services",
        "portfolio",
        "team",
        "faq",
        "why-ehteraf",
        "testimonials",
        "contact",
    }
    if page_name not in public_pages:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Page not found")
    return FileResponse(WEBSITE_ROOT / "index.html")
