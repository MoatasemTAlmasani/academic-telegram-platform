"""API route modules."""

from .auth import router as auth_router
from .dependencies import router as dependencies_router
from .health import router as health_router
from .rbac import router as rbac_router

__all__ = [
    "auth_router",
    "dependencies_router",
    "health_router",
    "rbac_router",
]
