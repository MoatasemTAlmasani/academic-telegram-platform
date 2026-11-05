"""Main API router."""

from fastapi import APIRouter

from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.admin_users import router as admin_users_router
from backend.app.api.routes.admin_staff import router as admin_staff_router
from backend.app.api.routes.admin_services import router as admin_services_router
from backend.app.api.routes.admin_telegram_destinations import telegram_destinations_router
from backend.app.api.routes.admin_telegram_destinations_verify import router as telegram_destinations_verify_router
from backend.app.api.routes.admin_requests import router as admin_requests_router
from backend.app.api.routes.admin_categories import router as admin_categories_router
from backend.app.api.routes.admin_settings import router as admin_settings_router
from backend.app.api.routes.admin_audit import router as admin_audit_router
from backend.app.api.routes.admin_dashboard import router as admin_dashboard_router
from backend.app.api.routes.dependencies import router as dependencies_router
from backend.app.api.routes.auth import router as auth_router
from backend.app.api.routes.rbac import router as rbac_router
from backend.app.api.routes.rbac_admin import router as rbac_admin_router
from backend.app.api.routes.telegram_webhook import router as telegram_webhook_router


from backend.app.api.routes.customer_requests import router as customer_requests_router
api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health_router)
api_router.include_router(admin_users_router)
api_router.include_router(admin_staff_router)
api_router.include_router(admin_services_router)
api_router.include_router(admin_requests_router)
api_router.include_router(admin_categories_router)
api_router.include_router(admin_settings_router)
api_router.include_router(admin_audit_router)
api_router.include_router(admin_dashboard_router)
api_router.include_router(dependencies_router)
api_router.include_router(auth_router)
api_router.include_router(rbac_router)
api_router.include_router(rbac_admin_router)
api_router.include_router(telegram_webhook_router)
api_router.include_router(telegram_destinations_router)
api_router.include_router(telegram_destinations_verify_router)
from backend.app.api.routes.public_services import router as public_services_router
api_router.include_router(public_services_router)
api_router.include_router(customer_requests_router)
