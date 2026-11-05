"""Read-only administrative dashboard aggregates.

All figures are derived from existing persisted domain records. Financial and
organizational metrics are explicitly unavailable until their source domains
exist; this module never substitutes demonstration values.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.api.auth_dependencies import get_current_user
from backend.app.api.rbac_dependencies import require_permission
from backend.app.infrastructure.persistence.database import get_session
from backend.app.modules.authentication.permissions import Permission
from database.models.audit import AuditLog
from database.models.catalog import Service
from database.models.enums import QuoteStatus, ServiceRequestStatus, UserStatus
from database.models.identity import Role, StaffProfile, User
from database.models.quotes import Quote
from database.models.requests import ServiceRequest


router = APIRouter(
    prefix="/admin/dashboard",
    tags=["admin-dashboard"],
)

ACTIVE_REQUEST_STATUSES = (
    ServiceRequestStatus.NEW,
    ServiceRequestStatus.UNDER_REVIEW,
    ServiceRequestStatus.WAITING_FOR_CUSTOMER,
    ServiceRequestStatus.QUOTATION_SENT,
    ServiceRequestStatus.APPROVED,
    ServiceRequestStatus.IN_PROGRESS,
)
TERMINAL_REQUEST_STATUSES = (
    ServiceRequestStatus.COMPLETED,
    ServiceRequestStatus.CANCELLED,
    ServiceRequestStatus.REJECTED,
)


async def _count(session: AsyncSession, statement) -> int:
    result = await session.execute(statement)
    return int(result.scalar_one() or 0)


@router.get(
    "/overview",
    dependencies=[Depends(require_permission(Permission.ADMIN_ACCESS))],
)
async def get_admin_dashboard_overview(
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Return real dashboard KPIs, trends, queues, and recent activity."""

    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)

    customer_scope = (
        select(User.id)
        .join(User.roles)
        .where(
            Role.name == "customer",
            User.deleted_at.is_(None),
        )
    )
    total_customers = await _count(
        session,
        select(func.count(func.distinct(User.id)))
        .select_from(User)
        .join(User.roles)
        .where(Role.name == "customer", User.deleted_at.is_(None)),
    )
    new_customers = await _count(
        session,
        select(func.count(func.distinct(User.id)))
        .select_from(User)
        .join(User.roles)
        .where(
            Role.name == "customer",
            User.deleted_at.is_(None),
            User.created_at >= thirty_days_ago,
        ),
    )

    total_services = await _count(
        session,
        select(func.count(Service.id)).where(Service.deleted_at.is_(None)),
    )
    active_services = await _count(
        session,
        select(func.count(Service.id)).where(
            Service.deleted_at.is_(None),
            Service.is_active.is_(True),
        ),
    )

    request_scope = ServiceRequest.deleted_at.is_(None)
    total_requests = await _count(
        session,
        select(func.count(ServiceRequest.id)).where(request_scope),
    )
    active_requests = await _count(
        session,
        select(func.count(ServiceRequest.id)).where(
            request_scope,
            ServiceRequest.status.in_(ACTIVE_REQUEST_STATUSES),
        ),
    )
    completed_requests = await _count(
        session,
        select(func.count(ServiceRequest.id)).where(
            request_scope,
            ServiceRequest.status == ServiceRequestStatus.COMPLETED,
        ),
    )
    overdue_requests = await _count(
        session,
        select(func.count(ServiceRequest.id)).where(
            request_scope,
            ServiceRequest.deadline.is_not(None),
            ServiceRequest.deadline < now,
            ServiceRequest.status.not_in(TERMINAL_REQUEST_STATUSES),
        ),
    )

    active_staff = await _count(
        session,
        select(func.count(func.distinct(User.id)))
        .select_from(User)
        .join(User.roles)
        .join(StaffProfile, StaffProfile.user_id == User.id)
        .where(
            Role.name == "staff",
            User.deleted_at.is_(None),
            User.status == UserStatus.ACTIVE,
            StaffProfile.is_active.is_(True),
        ),
    )

    pending_quotations = await _count(
        session,
        select(func.count(Quote.id)).where(
            Quote.deleted_at.is_(None),
            Quote.status == QuoteStatus.SENT,
        ),
    )

    status_result = await session.execute(
        select(ServiceRequest.status, func.count(ServiceRequest.id))
        .where(request_scope)
        .group_by(ServiceRequest.status)
    )
    requests_by_status = [
        {
            "status": status.value if hasattr(status, "value") else str(status),
            "count": int(count),
        }
        for status, count in status_result.all()
    ]

    trend_result = await session.execute(
        select(
            func.date(ServiceRequest.created_at).label("day"),
            func.count(ServiceRequest.id).label("count"),
        )
        .where(
            request_scope,
            ServiceRequest.created_at >= thirty_days_ago,
        )
        .group_by(func.date(ServiceRequest.created_at))
        .order_by(func.date(ServiceRequest.created_at))
    )
    requests_trend = [
        {"date": str(day), "count": int(count)}
        for day, count in trend_result.all()
    ]

    service_result = await session.execute(
        select(Service.name, func.count(ServiceRequest.id).label("count"))
        .join(ServiceRequest, ServiceRequest.service_id == Service.id)
        .where(
            request_scope,
            Service.deleted_at.is_(None),
        )
        .group_by(Service.id, Service.name)
        .order_by(func.count(ServiceRequest.id).desc())
        .limit(8)
    )
    requests_by_service = [
        {"service": name, "count": int(count)}
        for name, count in service_result.all()
    ]

    recent_request_result = await session.execute(
        select(ServiceRequest)
        .options(
            selectinload(ServiceRequest.customer),
            selectinload(ServiceRequest.service),
        )
        .where(request_scope)
        .order_by(ServiceRequest.created_at.desc())
        .limit(8)
    )
    recent_requests = []
    for item in recent_request_result.scalars().all():
        customer = item.customer
        customer_name = (
            " ".join(
                part for part in (
                    getattr(customer, "first_name", None),
                    getattr(customer, "last_name", None),
                ) if part
            )
            or getattr(customer, "username", None)
            or "Customer"
        )
        recent_requests.append(
            {
                "id": str(item.id),
                "title": item.title,
                "customer": customer_name,
                "service": item.service.name if item.service else None,
                "status": (
                    item.status.value
                    if hasattr(item.status, "value")
                    else str(item.status)
                ),
                "priority": (
                    item.priority.value
                    if hasattr(item.priority, "value")
                    else str(item.priority)
                ),
                "deadline": item.deadline.isoformat() if item.deadline else None,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
        )

    activity_result = await session.execute(
        select(AuditLog)
        .options(selectinload(AuditLog.actor))
        .order_by(AuditLog.created_at.desc())
        .limit(10)
    )
    recent_activity = []
    for event in activity_result.scalars().all():
        actor = event.actor
        actor_name = (
            " ".join(
                part for part in (
                    getattr(actor, "first_name", None),
                    getattr(actor, "last_name", None),
                ) if part
            )
            or getattr(actor, "username", None)
            or "System"
        )
        recent_activity.append(
            {
                "id": str(event.id),
                "actor": actor_name,
                "action": event.action,
                "resource_type": event.resource_type,
                "resource_id": str(event.resource_id) if event.resource_id else None,
                "description": event.description,
                "created_at": event.created_at.isoformat(),
            }
        )

    return {
        "generated_at": now.isoformat(),
        "period": {"new_customers_days": 30, "request_trend_days": 30},
        "metrics": {
            "total_customers": total_customers,
            "new_customers": new_customers,
            "total_requests": total_requests,
            "active_requests": active_requests,
            "completed_requests": completed_requests,
            "overdue_requests": overdue_requests,
            "active_staff": active_staff,
            "total_services": total_services,
            "active_services": active_services,
            "pending_quotations": pending_quotations,
            "revenue": None,
            "outstanding_balance": None,
        },
        "availability": {
            "revenue": {
                "available": False,
                "reason": "No persisted invoice/payment ledger is implemented yet.",
            },
            "outstanding_balance": {
                "available": False,
                "reason": "No persisted receivables ledger is implemented yet.",
            },
            "staff_performance": {
                "available": False,
                "reason": "Requests are not yet assigned to staff in the current data model.",
            },
            "branch_performance": {
                "available": False,
                "reason": "Organization and branch data scopes are not yet implemented.",
            },
        },
        "requests_by_status": requests_by_status,
        "requests_trend": requests_trend,
        "requests_by_service": requests_by_service,
        "recent_requests": recent_requests,
        "recent_activity": recent_activity,
        "alerts": {
            "overdue_requests": overdue_requests,
            "pending_quotations": pending_quotations,
        },
    }
