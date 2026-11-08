"""Administrative dashboard APIs backed only by persisted platform records."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.app.api.auth_dependencies import get_current_user
from backend.app.api.rbac_dependencies import require_permission
from backend.app.infrastructure.persistence.database import get_session
from backend.app.modules.authentication.permissions import Permission
from database.models.audit import AuditLog
from database.models.catalog import Service
from database.models.enums import QuoteStatus, ServiceRequestStatus, UserStatus
from database.models.identity import Role, StaffProfile, User, UserSession
from database.models.quotes import Quote
from database.models.requests import ServiceRequest
from database.models.security import LoginAttempt
router = APIRouter(prefix="/admin/dashboard", tags=["admin-dashboard"])
ACTIVE = (ServiceRequestStatus.NEW, ServiceRequestStatus.UNDER_REVIEW, ServiceRequestStatus.WAITING_FOR_CUSTOMER, ServiceRequestStatus.QUOTATION_SENT, ServiceRequestStatus.APPROVED, ServiceRequestStatus.IN_PROGRESS)
TERMINAL = (ServiceRequestStatus.COMPLETED, ServiceRequestStatus.CANCELLED, ServiceRequestStatus.REJECTED)
async def count(session: AsyncSession, statement) -> int:
    result = await session.execute(statement)
    return int(result.scalar_one() or 0)
def has_dashboard_permission(permission_codes: set[str], permission: Permission) -> bool:
    """Check a persisted permission code before returning dashboard detail data."""
    return permission.value in permission_codes
@router.get("/access", dependencies=[Depends(require_permission(Permission.ADMIN_ACCESS))])
async def access_summary(current_user=Depends(get_current_user), session: AsyncSession=Depends(get_session)):
    result = await session.execute(select(User).options(selectinload(User.roles).selectinload(Role.permissions)).where(User.id == current_user.id))
    user = result.scalar_one()
    return {"user":{"id":str(user.id),"username":user.username,"first_name":user.first_name,"last_name":user.last_name,"email":user.email},"roles":sorted(r.name for r in user.roles),"permissions":sorted({p.code for r in user.roles for p in r.permissions})}
@router.get("/overview", dependencies=[Depends(require_permission(Permission.ADMIN_ACCESS))])
async def overview(period_days: int = Query(default=30, ge=7, le=365), service_id: UUID | None = Query(default=None), current_user=Depends(get_current_user), session: AsyncSession=Depends(get_session)):
    now=datetime.now(timezone.utc)
    since=now-timedelta(days=period_days)
    request_filters=[ServiceRequest.deleted_at.is_(None)]
    access_result=await session.execute(select(User).options(selectinload(User.roles).selectinload(Role.permissions)).where(User.id==current_user.id))
    access_user=access_result.scalar_one()
    user_permissions={permission.code for role in access_user.roles for permission in role.permissions}
    can_read_users=has_dashboard_permission(user_permissions,Permission.USERS_READ)
    can_read_requests=has_dashboard_permission(user_permissions,Permission.REQUESTS_READ)
    can_read_services=has_dashboard_permission(user_permissions,Permission.SERVICES_READ)
    can_read_quotes=has_dashboard_permission(user_permissions,Permission.QUOTES_READ)
    can_read_audit=has_dashboard_permission(user_permissions,Permission.AUDIT_READ)
    if service_id is not None:
        request_filters.append(ServiceRequest.service_id==service_id)
    metrics={}
    metrics["total_customers"]=await count(session,select(func.count(func.distinct(User.id))).select_from(User).join(User.roles).where(Role.name=="customer",User.deleted_at.is_(None)))
    metrics["new_customers"]=await count(session,select(func.count(func.distinct(User.id))).select_from(User).join(User.roles).where(Role.name=="customer",User.deleted_at.is_(None),User.created_at>=since))
    metrics["requests_in_period"]=await count(session,select(func.count(ServiceRequest.id)).where(*request_filters,ServiceRequest.created_at>=since))
    metrics["total_users"]=await count(session,select(func.count(User.id)).where(User.deleted_at.is_(None)))
    metrics["active_users"]=await count(session,select(func.count(User.id)).where(User.deleted_at.is_(None),User.status==UserStatus.ACTIVE))
    metrics["new_users"]=await count(session,select(func.count(User.id)).where(User.deleted_at.is_(None),User.created_at>=since))
    metrics["new_requests"]=metrics["requests_in_period"]
    metrics["total_services"]=await count(session,select(func.count(Service.id)).where(Service.deleted_at.is_(None)))
    metrics["active_services"]=await count(session,select(func.count(Service.id)).where(Service.deleted_at.is_(None),Service.is_active.is_(True)))
    metrics["total_requests"]=await count(session,select(func.count(ServiceRequest.id)).where(*request_filters))
    metrics["active_requests"]=await count(session,select(func.count(ServiceRequest.id)).where(*request_filters,ServiceRequest.status.in_(ACTIVE)))
    metrics["completed_requests"]=await count(session,select(func.count(ServiceRequest.id)).where(*request_filters,ServiceRequest.status==ServiceRequestStatus.COMPLETED))
    metrics["overdue_requests"]=await count(session,select(func.count(ServiceRequest.id)).where(*request_filters,ServiceRequest.deadline.is_not(None),ServiceRequest.deadline<now,ServiceRequest.status.not_in(TERMINAL)))
    metrics["active_staff"]=await count(session,select(func.count(func.distinct(User.id))).select_from(User).join(User.roles).join(StaffProfile,StaffProfile.user_id==User.id).where(Role.name=="staff",User.deleted_at.is_(None),User.status==UserStatus.ACTIVE,StaffProfile.is_active.is_(True)))
    metrics["pending_quotations"]=await count(session,select(func.count(Quote.id)).join(ServiceRequest,Quote.request_id==ServiceRequest.id).where(Quote.deleted_at.is_(None),Quote.status==QuoteStatus.SENT,*request_filters))
    # Dashboard access alone must not disclose aggregate data owned by other permissions.
    if not can_read_users:
        for key in ("total_customers", "new_customers", "total_users", "active_users", "new_users", "active_staff"):
            metrics[key]=None
    if not can_read_services:
        for key in ("total_services", "active_services"):
            metrics[key]=None
    if not can_read_requests:
        for key in ("requests_in_period", "new_requests", "total_requests", "active_requests", "completed_requests", "overdue_requests"):
            metrics[key]=None
    if not can_read_quotes:
        metrics["pending_quotations"]=None
    metrics["revenue"]=None
    metrics["outstanding_balance"]=None
    if can_read_requests:
        sr=await session.execute(select(ServiceRequest.status,func.count(ServiceRequest.id)).where(*request_filters,ServiceRequest.created_at>=since).group_by(ServiceRequest.status))
        by_status=[{"status":s.value,"count":int(n)} for s,n in sr.all()]
        tr=await session.execute(select(func.date(ServiceRequest.created_at),func.count(ServiceRequest.id)).where(*request_filters,ServiceRequest.created_at>=since).group_by(func.date(ServiceRequest.created_at)).order_by(func.date(ServiceRequest.created_at)))
        trend=[{"date":str(day),"count":int(n)} for day,n in tr.all()]
    else:
        by_status=[]
        trend=[]
    if can_read_requests and can_read_services:
        sv=await session.execute(select(Service.name,func.count(ServiceRequest.id)).join(ServiceRequest,ServiceRequest.service_id==Service.id).where(*request_filters,ServiceRequest.created_at>=since,Service.deleted_at.is_(None)).group_by(Service.id,Service.name).order_by(func.count(ServiceRequest.id).desc()).limit(8))
        by_service=[{"service":name,"count":int(n)} for name,n in sv.all()]
    else:
        by_service=[]
    recent=[]
    if can_read_requests:
        rr=await session.execute(select(ServiceRequest).options(selectinload(ServiceRequest.customer),selectinload(ServiceRequest.service)).where(*request_filters).order_by(ServiceRequest.created_at.desc()).limit(8))
        recent_rows=rr.scalars().all()
    else:
        recent_rows=[]
    for item in recent_rows:
        customer=item.customer
        cname=" ".join(x for x in (getattr(customer,"first_name",None),getattr(customer,"last_name",None)) if x) or getattr(customer,"username",None) or str(item.customer_id)
        recent.append({"id":str(item.id),"title":item.title,"customer":cname,"service":item.service.name if item.service else None,"status":item.status.value,"priority":item.priority.value,"deadline":item.deadline.isoformat() if item.deadline else None,"created_at":item.created_at.isoformat()})
    overdue_items=[]
    if can_read_requests:
        overdue_result=await session.execute(select(ServiceRequest).options(selectinload(ServiceRequest.customer)).where(*request_filters,ServiceRequest.deadline.is_not(None),ServiceRequest.deadline<now,ServiceRequest.status.not_in(TERMINAL)).order_by(ServiceRequest.deadline.asc()).limit(5))
        overdue_rows=overdue_result.scalars().all()
    else:
        overdue_rows=[]
    for item in overdue_rows:
        customer=item.customer
        customer_name=" ".join(x for x in (getattr(customer,"first_name",None),getattr(customer,"last_name",None)) if x) or getattr(customer,"username",None) or str(item.customer_id)
        overdue_items.append({"id":str(item.id),"title":item.title,"customer":customer_name,"deadline":item.deadline.isoformat(),"status":item.status.value})
    pending_quote_items=[]
    if can_read_quotes:
        pending_quote_result=await session.execute(select(Quote).join(ServiceRequest,Quote.request_id==ServiceRequest.id).options(selectinload(Quote.service_request)).where(Quote.deleted_at.is_(None),Quote.status==QuoteStatus.SENT,*request_filters).order_by(Quote.created_at.desc()).limit(5))
        pending_quote_rows=pending_quote_result.scalars().all()
    else:
        pending_quote_rows=[]
    for quote in pending_quote_rows:
        request=quote.service_request
        pending_quote_items.append({"id":str(quote.id),"quote_number":quote.quote_number,"request_id":str(quote.request_id),"request_title":request.title if request else "","expires_at":quote.expires_at.isoformat() if quote.expires_at else None})
    activity=[]
    if can_read_audit:
        ar=await session.execute(select(AuditLog).options(selectinload(AuditLog.actor)).order_by(AuditLog.created_at.desc()).limit(10))
        activity_rows=ar.scalars().all()
    else:
        activity_rows=[]
    for event in activity_rows:
        actor=event.actor
        aname=" ".join(x for x in (getattr(actor,"first_name",None),getattr(actor,"last_name",None)) if x) or getattr(actor,"username",None) or "System"
        activity.append({"id":str(event.id),"actor":aname,"action":event.action,"resource_type":event.resource_type,"resource_id":str(event.resource_id) if event.resource_id else None,"description":event.description,"created_at":event.created_at.isoformat()})
    if can_read_services:
        service_result=await session.execute(select(Service.id,Service.name).where(Service.deleted_at.is_(None),Service.is_active.is_(True)).order_by(Service.name.asc()))
        service_options=[{"id":str(service_key),"name":service_name} for service_key,service_name in service_result.all()]
    else:
        service_options=[]
    return {"generated_at":now.isoformat(),"period_days":period_days,"service_id":str(service_id) if service_id else None,"service_options":service_options,"metrics":metrics,"availability":{"total_customers":"Requires users:read permission.","new_customers":"Requires users:read permission.","total_users":"Requires users:read permission.","active_users":"Requires users:read permission.","new_users":"Requires users:read permission.","active_staff":"Requires users:read permission.","total_services":"Requires services:read permission.","active_services":"Requires services:read permission.","requests_in_period":"Requires requests:read permission.","new_requests":"Requires requests:read permission.","total_requests":"Requires requests:read permission.","active_requests":"Requires requests:read permission.","completed_requests":"Requires requests:read permission.","overdue_requests":"Requires requests:read permission.","pending_quotations":"Requires quotes:read permission.","revenue":"Unavailable until an invoice/payment ledger exists.","outstanding_balance":"Unavailable until receivables are implemented.","staff_performance":"Unavailable until requests support staff assignment.","branch_performance":"Unavailable until organization and branch scopes exist."},"requests_by_status":by_status,"requests_trend":trend,"requests_by_service":by_service,"recent_requests":recent,"recent_activity":activity,"overdue_items":overdue_items,"pending_quotation_items":pending_quote_items,"alerts":{"overdue_requests":metrics["overdue_requests"],"pending_quotations":metrics["pending_quotations"]}}


@router.get(
    "/security/overview",
    dependencies=[Depends(require_permission(Permission.USERS_READ))],
)
async def security_overview(
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Return platform-wide security indicators from persisted records only."""
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(hours=24)
    active_sessions = await count(
        session,
        select(func.count(UserSession.id)).where(
            UserSession.revoked_at.is_(None), UserSession.expires_at > now
        ),
    )
    failed_logins = await count(
        session,
        select(func.count(LoginAttempt.id)).where(
            LoginAttempt.succeeded.is_(False), LoginAttempt.attempted_at >= day_ago
        ),
    )
    locked_accounts = await count(
        session,
        select(func.count(User.id)).where(
            User.deleted_at.is_(None), User.locked_until.is_not(None), User.locked_until > now
        ),
    )
    suspended_accounts = await count(
        session,
        select(func.count(User.id)).where(
            User.deleted_at.is_(None), User.status == UserStatus.SUSPENDED
        ),
    )
    recent_result = await session.execute(
        select(LoginAttempt, User.username, User.first_name, User.last_name)
        .outerjoin(User, User.id == LoginAttempt.user_id)
        .where(
            LoginAttempt.succeeded.is_(False),
            LoginAttempt.attempted_at >= now - timedelta(days=7),
        )
        .order_by(LoginAttempt.attempted_at.desc())
        .limit(10)
    )
    recent_failed_logins = []
    for attempt, username, first_name, last_name in recent_result.all():
        display_name = " ".join(part for part in (first_name, last_name) if part)
        recent_failed_logins.append(
            {
                "id": str(attempt.id),
                "identity": display_name or username or attempt.username_key,
                "ip_address": attempt.ip_address,
                "attempted_at": attempt.attempted_at.isoformat() if attempt.attempted_at else None,
            }
        )
    return {
        "generated_at": now.isoformat(),
        "metrics": {
            "active_sessions": active_sessions,
            "failed_logins_24h": failed_logins,
            "locked_accounts": locked_accounts,
            "suspended_accounts": suspended_accounts,
        },
        "recent_failed_logins": recent_failed_logins,
    }


@router.get(
    "/security/sessions",
    dependencies=[Depends(require_permission(Permission.USERS_READ))],
)
async def list_platform_security_sessions(
    status: str = Query(default="active", pattern="^(active|revoked|expired|all)$"),
    search: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=50, ge=1, le=100),
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List sessions across users without exposing credentials or token material."""
    now = datetime.now(timezone.utc)
    statement = (
        select(UserSession, User)
        .join(User, User.id == UserSession.user_id)
        .where(User.deleted_at.is_(None))
    )
    if status == "active":
        statement = statement.where(
            UserSession.revoked_at.is_(None), UserSession.expires_at > now
        )
    elif status == "revoked":
        statement = statement.where(UserSession.revoked_at.is_not(None))
    elif status == "expired":
        statement = statement.where(
            UserSession.revoked_at.is_(None), UserSession.expires_at <= now
        )
    if search:
        pattern = f"%{search.strip()}%"
        statement = statement.where(
            or_(
                User.username.ilike(pattern),
                User.email.ilike(pattern),
                User.first_name.ilike(pattern),
                User.last_name.ilike(pattern),
                UserSession.ip_address.ilike(pattern),
            )
        )
    statement = statement.order_by(UserSession.created_at.desc()).limit(limit)
    result = await session.execute(statement)
    rows = result.all()
    items = []
    for item, user in rows:
        name = " ".join(part for part in (user.first_name, user.last_name) if part)
        expires_at = item.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        is_active = item.revoked_at is None and expires_at > now
        items.append(
            {
                "id": str(item.id),
                "user_id": str(user.id),
                "user_name": name or user.username or user.email or str(user.id),
                "username": user.username,
                "email": user.email,
                "ip_address": item.ip_address,
                "user_agent": item.user_agent,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "last_seen_at": item.last_seen_at.isoformat() if item.last_seen_at else None,
                "expires_at": item.expires_at.isoformat() if item.expires_at else None,
                "revoked_at": item.revoked_at.isoformat() if item.revoked_at else None,
                "revoked_reason": item.revoked_reason,
                "is_active": is_active,
                "can_revoke": is_active and user.id != current_user.id,
                "is_own_account": user.id == current_user.id,
            }
        )
    return {"items": items, "count": len(items), "status": status}


@router.post(
    "/security/sessions/{session_id}/revoke",
    dependencies=[Depends(require_permission(Permission.USERS_UPDATE))],
)
async def revoke_platform_security_session(
    session_id: UUID,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Revoke one other user's active session and write an immutable audit event."""
    item = await session.get(UserSession, session_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    if item.user_id == current_user.id:
        raise HTTPException(status_code=409, detail="You cannot revoke your own session here.")
    now = datetime.now(timezone.utc)
    expires_at = item.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if item.revoked_at is not None or expires_at <= now:
        raise HTTPException(status_code=409, detail="Session is no longer active.")
    revoke_result = await session.execute(
        update(UserSession)
        .where(
            UserSession.id == session_id,
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > now,
        )
        .values(revoked_at=now, revoked_reason="revoked_by_admin")
        .execution_options(synchronize_session=False)
    )
    if revoke_result.rowcount != 1:
        raise HTTPException(status_code=409, detail="Session is no longer active.")
    session.add(
        AuditLog(
            actor_id=current_user.id,
            action="security.session.revoked",
            resource_type="user_session",
            resource_id=item.id,
            description="Administrator revoked an active user session.",
            event_metadata={"target_user_id": str(item.user_id)},
            created_at=now,
        )
    )
    await session.commit()
    return {"status": "revoked", "session_id": str(item.id)}
