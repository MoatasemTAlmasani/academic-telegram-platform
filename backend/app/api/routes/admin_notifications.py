"""Administrative in-app notification management."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.auth_dependencies import get_current_user
from backend.app.api.rbac_dependencies import require_permission
from backend.app.infrastructure.persistence.database import get_session
from backend.app.modules.authentication.permissions import Permission
from database.models.audit import AuditLog
from database.models.enums import UserStatus
from database.models.identity import User
from database.models.notifications import Notification

admin_router = APIRouter(prefix="/admin/notifications", tags=["admin-notifications"])
user_router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    message: str = Field(min_length=1, max_length=10000)
    target_user_id: UUID | None = None
    broadcast: bool = False


@admin_router.get("/recipients", dependencies=[Depends(require_permission(Permission.ADMIN_ACCESS))])
async def notification_recipients(search: str | None = Query(default=None, max_length=200), session: AsyncSession = Depends(get_session)):
    query = select(User.id, User.username, User.email).where(User.status == UserStatus.ACTIVE)
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.where(or_(User.username.ilike(term), User.email.ilike(term)))
    rows = (await session.execute(query.order_by(User.username).limit(100))).all()
    return {"items": [{"id": str(row.id), "username": row.username, "email": row.email} for row in rows]}


@admin_router.get("", dependencies=[Depends(require_permission(Permission.ADMIN_ACCESS))])
async def list_notifications(
    status: str | None = Query(default=None, max_length=50),
    search: str | None = Query(default=None, max_length=200),
    offset: int = Query(default=0, ge=0, le=100000),
    limit: int = Query(default=25, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    filters = [Notification.channel == "in_app"]
    if status:
        filters.append(Notification.status == status.upper())
    if search:
        term = f"%{search.strip()}%"
        filters.append(or_(Notification.title.ilike(term), Notification.message.ilike(term)))

    total = int((await session.execute(select(func.count(Notification.id)).where(*filters))).scalar_one() or 0)
    rows = (await session.execute(
        select(Notification, User.username, User.email)
        .join(User, User.id == Notification.user_id)
        .where(*filters)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .offset(offset)
        .limit(limit)
    )).all()
    return {
        "items": [
            {
                "id": str(item.id),
                "user_id": str(item.user_id),
                "username": username,
                "email": email,
                "title": item.title,
                "message": item.message,
                "channel": item.channel,
                "status": item.status,
                "created_at": item.created_at,
                "sent_at": item.sent_at,
            }
            for item, username, email in rows
        ],
        "total": total,
        "offset": offset,
        "limit": limit,
    }


@admin_router.post("", status_code=201, dependencies=[Depends(require_permission(Permission.ADMIN_ACCESS))])
async def create_notification(
    payload: NotificationCreate,
    actor=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    title = payload.title.strip()
    message = payload.message.strip()
    if not title or not message:
        raise HTTPException(status_code=422, detail="Title and message must not be blank.")
    if payload.broadcast == (payload.target_user_id is not None):
        raise HTTPException(status_code=422, detail="Choose exactly one recipient: a user or all active users.")

    now = datetime.now(timezone.utc)
    if payload.broadcast:
        recipient_ids = list((await session.execute(
            select(User.id).where(User.status == UserStatus.ACTIVE).order_by(User.id).limit(2001)
        )).scalars().all())
        if len(recipient_ids) > 2000:
            raise HTTPException(status_code=409, detail="Broadcast is limited to 2000 active accounts per request.")
        if not recipient_ids:
            raise HTTPException(status_code=409, detail="There are no active accounts to notify.")
    else:
        recipient = await session.get(User, payload.target_user_id)
        if recipient is None or recipient.status != UserStatus.ACTIVE:
            raise HTTPException(status_code=404, detail="Active recipient account was not found.")
        recipient_ids = [recipient.id]

    notifications = [
        Notification(
            id=uuid4(),
            user_id=user_id,
            channel="in_app",
            title=title,
            message=message,
            status="SENT",
            payload={"source": "admin_console"},
            created_at=now,
            sent_at=now,
        )
        for user_id in recipient_ids
    ]
    session.add_all(notifications)
    session.add(AuditLog(
        actor_id=actor.id,
        action="notification.broadcast_created" if payload.broadcast else "notification.created",
        resource_type="notification",
        resource_id=notifications[0].id if len(notifications) == 1 else None,
        description=f"Created in-app notification for {len(notifications)} account(s).",
        event_metadata={"recipient_count": len(notifications), "broadcast": payload.broadcast},
        created_at=now,
    ))
    await session.commit()
    return {"created": len(notifications), "channel": "in_app", "status": "SENT"}


@user_router.get("/me")
async def my_notifications(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=100000),
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    filters = (Notification.user_id == current_user.id, Notification.channel == "in_app")
    total = int((await session.execute(select(func.count(Notification.id)).where(*filters))).scalar_one() or 0)
    items = (await session.execute(
        select(Notification).where(*filters)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .offset(offset).limit(limit)
    )).scalars().all()
    return {
        "items": [
            {
                "id": str(item.id),
                "title": item.title,
                "message": item.message,
                "created_at": item.created_at,
                "status": item.status,
            }
            for item in items
        ],
        "total": total,
        "offset": offset,
        "limit": limit,
    }
