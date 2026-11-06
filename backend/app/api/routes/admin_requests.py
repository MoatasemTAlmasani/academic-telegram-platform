from __future__ import annotations
import urllib.request
import urllib.parse
import json
import asyncio
import os
"""Admin service requests management API."""


from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.api.auth_dependencies import get_current_user
from backend.app.api.rbac_dependencies import require_permission
from backend.app.infrastructure.persistence.database import get_session
from backend.app.modules.authentication.permissions import Permission
from database.models.enums import RequestPriority, ServiceRequestStatus
from database.models.audit import AuditLog
from database.models.requests import ServiceRequest


router = APIRouter(
    prefix="/admin/requests",
    tags=["admin-requests"],
)


class RequestListItem(BaseModel):
    id: UUID
    title: str
    description: str | None = None
    specialization: str | None = None
    deadline: str | None = None
    status: ServiceRequestStatus
    priority: RequestPriority
    customer_id: UUID
    service_id: UUID
    created_at: str


class RequestListResponse(BaseModel):
    items: list[RequestListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


@router.get(
    "",
    response_model=RequestListResponse,
    dependencies=[
        Depends(require_permission(Permission.REQUESTS_READ)),
    ],
)
async def list_admin_requests(
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=255),
    status: ServiceRequestStatus | None = None,
    priority: RequestPriority | None = None,
):
    query = (
        select(ServiceRequest)
        .where(ServiceRequest.deleted_at.is_(None))
        .order_by(ServiceRequest.created_at.desc())
    )

    count_query = (
        select(func.count(ServiceRequest.id))
        .where(ServiceRequest.deleted_at.is_(None))
    )

    if search:
        pattern = f"%{search.strip()}%"
        condition = or_(
            ServiceRequest.title.ilike(pattern),
            ServiceRequest.description.ilike(pattern),
            ServiceRequest.specialization.ilike(pattern),
        )
        query = query.where(condition)
        count_query = count_query.where(condition)

    if status is not None:
        query = query.where(ServiceRequest.status == status)
        count_query = count_query.where(ServiceRequest.status == status)

    if priority is not None:
        query = query.where(ServiceRequest.priority == priority)
        count_query = count_query.where(ServiceRequest.priority == priority)

    total = (await session.execute(count_query)).scalar_one()

    result = await session.execute(
        query.offset((page - 1) * page_size).limit(page_size)
    )

    requests = result.scalars().all()

    return RequestListResponse(
        items=[
            RequestListItem(
                id=item.id,
                title=item.title,
                description=item.description,
                specialization=item.specialization,
                deadline=item.deadline.isoformat() if item.deadline else None,
                status=item.status,
                priority=item.priority,
                customer_id=item.customer_id,
                service_id=item.service_id,
                created_at=item.created_at.isoformat(),
            )
            for item in requests
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get(
    "/{request_id}",
    dependencies=[Depends(require_permission(Permission.REQUESTS_READ))],
)
async def get_admin_request_details(
    request_id: UUID,
    session=Depends(get_session),
):
    from fastapi import HTTPException
    from database.models.requests import ServiceRequest

    request = await session.get(ServiceRequest, request_id)

    if request is None or getattr(request, "deleted_at", None) is not None:
        raise HTTPException(status_code=404, detail="Request not found")

    return {
        "id": str(request.id),
        "title": request.title,
        "description": request.description,
        "specialization": request.specialization,
        "deadline": request.deadline.isoformat() if request.deadline else None,
        "status": request.status.value if hasattr(request.status, "value") else str(request.status),
        "priority": request.priority.value if hasattr(request.priority, "value") else str(request.priority),
        "notes": request.notes,
        "customer_id": str(request.customer_id),
        "service_id": str(request.service_id),
        "created_at": request.created_at.isoformat() if request.created_at else None,
    }


@router.patch(
    "/{request_id}",
    dependencies=[Depends(require_permission(Permission.REQUESTS_UPDATE))],
)
async def update_admin_request(
    request_id: UUID,
    payload: dict,
    session=Depends(get_session),
):
    from fastapi import HTTPException
    from database.models.requests import ServiceRequest, ServiceRequestStatus, RequestPriority

    request = await session.get(ServiceRequest, request_id)

    if request is None or getattr(request, "deleted_at", None) is not None:
        raise HTTPException(status_code=404, detail="Request not found")

    original_status = (
        request.status.value
        if hasattr(request.status, "value")
        else str(request.status)
    )

    if "status" in payload and payload["status"]:
        try:
            request.status = ServiceRequestStatus(payload["status"])
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status")

    if "priority" in payload and payload["priority"]:
        try:
            request.priority = RequestPriority(payload["priority"])
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid priority")

    if "notes" in payload:
        request.notes = payload["notes"] or None

    new_status = (
        request.status.value
        if hasattr(request.status, "value")
        else str(request.status)
    )
    status_changed = original_status != new_status


    # Detect status change and notify customer after successful update
    # The original status is captured from the request object before mutation.
    # This variable is populated below when the endpoint is patched.
    await session.commit()
    await session.refresh(request)

    # Telegram customer notification
    if status_changed:
        try:
            from database.models.identity import User

            customer = await session.get(User, request.customer_id)

            if customer:
                chat_id = None

                # Support common Telegram chat-id field names
                for field_name in (
                    "telegram_chat_id",
                    "telegram_id",
                    "chat_id",
                    "telegram_user_id",
                ):
                    if hasattr(customer, field_name):
                        value = getattr(customer, field_name, None)
                        if value:
                            chat_id = str(value)
                            break

                bot_token = (
                    os.getenv("TELEGRAM_BOT_TOKEN")
                    or os.getenv("BOT_TOKEN")
                )

                if chat_id and bot_token:
                    status_names = {
                        "NEW": "🆕 طلب جديد",
                        "UNDER_REVIEW": "🔎 قيد المراجعة",
                        "WAITING_FOR_CUSTOMER": "⏳ بانتظار العميل",
                        "QUOTATION_SENT": "💰 تم إرسال عرض السعر",
                        "APPROVED": "✅ تمت الموافقة",
                        "IN_PROGRESS": "⚙️ قيد التنفيذ",
                        "COMPLETED": "🎉 مكتمل",
                        "CANCELLED": "❌ ملغي",
                        "REJECTED": "🚫 مرفوض",
                    }

                    status_value = (
                        request.status.value
                        if hasattr(request.status, "value")
                        else str(request.status)
                    )

                    status_text = status_names.get(
                        status_value,
                        status_value
                    )

                    message = (
                        "🔔 <b>تحديث طلبك</b>\n\n"
                        f"📌 <b>الطلب:</b> {request.title}\n"
                        f"📊 <b>الحالة الجديدة:</b> {status_text}\n\n"
                        "يمكنك التواصل معنا إذا كان لديك أي استفسار."
                    )

                    data = urllib.parse.urlencode({
                        "chat_id": chat_id,
                        "text": message,
                        "parse_mode": "HTML",
                    }).encode()

                    url = (
                        "https://api.telegram.org/bot"
                        + bot_token
                        + "/sendMessage"
                    )

                    def send_telegram():
                        req = urllib.request.Request(
                            url,
                            data=data,
                            method="POST",
                            headers={
                                "Content-Type":
                                "application/x-www-form-urlencoded"
                            },
                        )
                        with urllib.request.urlopen(req, timeout=10) as response:
                            return response.read()

                    await asyncio.to_thread(send_telegram)

                    print(
                        f"TELEGRAM STATUS NOTIFICATION SENT: "
                        f"request={request.id} chat_id={chat_id}"
                    )

        except Exception as telegram_error:
            # Telegram failure must NOT rollback the successfully saved request.
            print(
                f"TELEGRAM STATUS NOTIFICATION FAILED: "
                f"request={request.id} error={telegram_error}"
            )

    return {
        "success": True,
        "message": "Request updated successfully",
        "id": str(request.id),
        "status": request.status.value if hasattr(request.status, "value") else str(request.status),
        "priority": request.priority.value if hasattr(request.priority, "value") else str(request.priority),
        "notes": request.notes,
    }


@router.delete(
    "/{request_id}",
    status_code=204,
    dependencies=[Depends(require_permission(Permission.REQUESTS_UPDATE))],
)
async def archive_admin_request(
    request_id: UUID,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    request = await session.scalar(
        select(ServiceRequest).where(
            ServiceRequest.id == request_id,
            ServiceRequest.deleted_at.is_(None),
        )
    )
    if request is None:
        raise HTTPException(status_code=404, detail="Request not found.")
    now = datetime.now(timezone.utc)
    request.deleted_at = now
    session.add(AuditLog(
        actor_id=current_user.id,
        action="request.archived",
        resource_type="service_request",
        resource_id=request.id,
        description=f"Admin archived request '{request.title}'.",
        event_metadata={"request_id": str(request.id)},
        created_at=now,
    ))
    await session.commit()
    return Response(status_code=204)
