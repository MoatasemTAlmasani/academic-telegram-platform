"""Administrative dashboard APIs backed only by persisted platform records."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
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
router = APIRouter(prefix="/admin/dashboard", tags=["admin-dashboard"])
ACTIVE = (ServiceRequestStatus.NEW, ServiceRequestStatus.UNDER_REVIEW, ServiceRequestStatus.WAITING_FOR_CUSTOMER, ServiceRequestStatus.QUOTATION_SENT, ServiceRequestStatus.APPROVED, ServiceRequestStatus.IN_PROGRESS)
TERMINAL = (ServiceRequestStatus.COMPLETED, ServiceRequestStatus.CANCELLED, ServiceRequestStatus.REJECTED)
async def count(session: AsyncSession, statement) -> int:
    result = await session.execute(statement)
    return int(result.scalar_one() or 0)
@router.get("/access", dependencies=[Depends(require_permission(Permission.ADMIN_ACCESS))])
async def access_summary(current_user=Depends(get_current_user), session: AsyncSession=Depends(get_session)):
    result = await session.execute(select(User).options(selectinload(User.roles).selectinload(Role.permissions)).where(User.id == current_user.id))
    user = result.scalar_one()
    return {"user":{"id":str(user.id),"username":user.username,"first_name":user.first_name,"last_name":user.last_name,"email":user.email},"roles":sorted(r.name for r in user.roles),"permissions":sorted({p.code for r in user.roles for p in r.permissions})}
@router.get("/overview", dependencies=[Depends(require_permission(Permission.ADMIN_ACCESS))])
async def overview(period_days: int = Query(default=30, ge=7, le=365), current_user=Depends(get_current_user), session: AsyncSession=Depends(get_session)):
    now=datetime.now(timezone.utc)
    since=now-timedelta(days=period_days)
    metrics={}
    metrics["total_customers"]=await count(session,select(func.count(func.distinct(User.id))).select_from(User).join(User.roles).where(Role.name=="customer",User.deleted_at.is_(None)))
    metrics["new_customers"]=await count(session,select(func.count(func.distinct(User.id))).select_from(User).join(User.roles).where(Role.name=="customer",User.deleted_at.is_(None),User.created_at>=since))
    metrics["requests_in_period"]=await count(session,select(func.count(ServiceRequest.id)).where(ServiceRequest.deleted_at.is_(None),ServiceRequest.created_at>=since))
    metrics["total_users"]=await count(session,select(func.count(User.id)).where(User.deleted_at.is_(None)))
    metrics["active_users"]=await count(session,select(func.count(User.id)).where(User.deleted_at.is_(None),User.status==UserStatus.ACTIVE))
    metrics["new_users"]=await count(session,select(func.count(User.id)).where(User.deleted_at.is_(None),User.created_at>=since))
    metrics["new_requests"]=metrics["requests_in_period"]
    metrics["total_services"]=await count(session,select(func.count(Service.id)).where(Service.deleted_at.is_(None)))
    metrics["active_services"]=await count(session,select(func.count(Service.id)).where(Service.deleted_at.is_(None),Service.is_active.is_(True)))
    metrics["total_requests"]=await count(session,select(func.count(ServiceRequest.id)).where(ServiceRequest.deleted_at.is_(None)))
    metrics["active_requests"]=await count(session,select(func.count(ServiceRequest.id)).where(ServiceRequest.deleted_at.is_(None),ServiceRequest.status.in_(ACTIVE)))
    metrics["completed_requests"]=await count(session,select(func.count(ServiceRequest.id)).where(ServiceRequest.deleted_at.is_(None),ServiceRequest.status==ServiceRequestStatus.COMPLETED))
    metrics["overdue_requests"]=await count(session,select(func.count(ServiceRequest.id)).where(ServiceRequest.deleted_at.is_(None),ServiceRequest.deadline.is_not(None),ServiceRequest.deadline<now,ServiceRequest.status.not_in(TERMINAL)))
    metrics["active_staff"]=await count(session,select(func.count(func.distinct(User.id))).select_from(User).join(User.roles).join(StaffProfile,StaffProfile.user_id==User.id).where(Role.name=="staff",User.deleted_at.is_(None),User.status==UserStatus.ACTIVE,StaffProfile.is_active.is_(True)))
    metrics["pending_quotations"]=await count(session,select(func.count(Quote.id)).where(Quote.deleted_at.is_(None),Quote.status==QuoteStatus.SENT))
    metrics["revenue"]=None
    metrics["outstanding_balance"]=None
    sr=await session.execute(select(ServiceRequest.status,func.count(ServiceRequest.id)).where(ServiceRequest.deleted_at.is_(None),ServiceRequest.created_at>=since).group_by(ServiceRequest.status))
    by_status=[{"status":s.value,"count":int(n)} for s,n in sr.all()]
    tr=await session.execute(select(func.date(ServiceRequest.created_at),func.count(ServiceRequest.id)).where(ServiceRequest.deleted_at.is_(None),ServiceRequest.created_at>=since).group_by(func.date(ServiceRequest.created_at)).order_by(func.date(ServiceRequest.created_at)))
    trend=[{"date":str(day),"count":int(n)} for day,n in tr.all()]
    sv=await session.execute(select(Service.name,func.count(ServiceRequest.id)).join(ServiceRequest,ServiceRequest.service_id==Service.id).where(ServiceRequest.deleted_at.is_(None),ServiceRequest.created_at>=since,Service.deleted_at.is_(None)).group_by(Service.id,Service.name).order_by(func.count(ServiceRequest.id).desc()).limit(8))
    by_service=[{"service":name,"count":int(n)} for name,n in sv.all()]
    rr=await session.execute(select(ServiceRequest).options(selectinload(ServiceRequest.customer),selectinload(ServiceRequest.service)).where(ServiceRequest.deleted_at.is_(None)).order_by(ServiceRequest.created_at.desc()).limit(8))
    recent=[]
    for item in rr.scalars().all():
        customer=item.customer
        cname=" ".join(x for x in (getattr(customer,"first_name",None),getattr(customer,"last_name",None)) if x) or getattr(customer,"username",None) or str(item.customer_id)
        recent.append({"id":str(item.id),"title":item.title,"customer":cname,"service":item.service.name if item.service else None,"status":item.status.value,"priority":item.priority.value,"deadline":item.deadline.isoformat() if item.deadline else None,"created_at":item.created_at.isoformat()})
    overdue_result=await session.execute(select(ServiceRequest).options(selectinload(ServiceRequest.customer)).where(ServiceRequest.deleted_at.is_(None),ServiceRequest.deadline.is_not(None),ServiceRequest.deadline<now,ServiceRequest.status.not_in(TERMINAL)).order_by(ServiceRequest.deadline.asc()).limit(5))
    overdue_items=[]
    for item in overdue_result.scalars().all():
        customer=item.customer
        customer_name=" ".join(x for x in (getattr(customer,"first_name",None),getattr(customer,"last_name",None)) if x) or getattr(customer,"username",None) or str(item.customer_id)
        overdue_items.append({"id":str(item.id),"title":item.title,"customer":customer_name,"deadline":item.deadline.isoformat(),"status":item.status.value})
    pending_quote_result=await session.execute(select(Quote).options(selectinload(Quote.service_request)).where(Quote.deleted_at.is_(None),Quote.status==QuoteStatus.SENT).order_by(Quote.created_at.desc()).limit(5))
    pending_quote_items=[]
    for quote in pending_quote_result.scalars().all():
        request=quote.service_request
        pending_quote_items.append({"id":str(quote.id),"quote_number":quote.quote_number,"request_id":str(quote.request_id),"request_title":request.title if request else "","expires_at":quote.expires_at.isoformat() if quote.expires_at else None})
    ar=await session.execute(select(AuditLog).options(selectinload(AuditLog.actor)).order_by(AuditLog.created_at.desc()).limit(10))
    activity=[]
    for event in ar.scalars().all():
        actor=event.actor
        aname=" ".join(x for x in (getattr(actor,"first_name",None),getattr(actor,"last_name",None)) if x) or getattr(actor,"username",None) or "System"
        activity.append({"id":str(event.id),"actor":aname,"action":event.action,"resource_type":event.resource_type,"resource_id":str(event.resource_id) if event.resource_id else None,"description":event.description,"created_at":event.created_at.isoformat()})
    return {"generated_at":now.isoformat(),"period_days":period_days,"metrics":metrics,"availability":{"revenue":"Unavailable until an invoice/payment ledger exists.","outstanding_balance":"Unavailable until receivables are implemented.","staff_performance":"Unavailable until requests support staff assignment.","branch_performance":"Unavailable until organization and branch scopes exist."},"requests_by_status":by_status,"requests_trend":trend,"requests_by_service":by_service,"recent_requests":recent,"recent_activity":activity,"overdue_items":overdue_items,"pending_quotation_items":pending_quote_items,"alerts":{"overdue_requests":metrics["overdue_requests"],"pending_quotations":metrics["pending_quotations"]}}
