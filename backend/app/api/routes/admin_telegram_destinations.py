"""Admin Telegram destinations management API."""

from __future__ import annotations

from uuid import UUID
import csv
import io

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.auth_dependencies import get_current_user
from backend.app.api.rbac_dependencies import require_permission
from backend.app.infrastructure.persistence.database import get_session
from backend.app.modules.authentication.permissions import Permission
from database.models.telegram import TelegramDestination


telegram_destinations_router = APIRouter(
    prefix="/admin/telegram-destinations",
    tags=["admin-telegram-destinations"],
)


class TelegramDestinationResponse(BaseModel):
    id: UUID
    original_url: str
    normalized_identifier: str | None = None
    chat_id: int | None = None
    username: str | None = None
    title: str | None = None
    chat_type: str
    privacy_status: str
    bot_status: str
    can_post: bool | None = None
    is_active: bool
    validation_status: str
    last_checked_at: str | None = None
    last_success_at: str | None = None
    last_error: str | None = None


class TelegramDestinationListResponse(BaseModel):
    items: list[TelegramDestinationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class TelegramDestinationCreateRequest(BaseModel):
    original_url: str
    title: str | None = None
    is_active: bool = True


class TelegramDestinationUpdateRequest(BaseModel):
    original_url: str | None = None
    title: str | None = None
    is_active: bool | None = None


def destination_response(
    destination: TelegramDestination,
) -> TelegramDestinationResponse:
    return TelegramDestinationResponse(
        id=destination.id,
        original_url=destination.original_url,
        normalized_identifier=destination.normalized_identifier,
        chat_id=destination.chat_id,
        username=destination.username,
        title=destination.title,
        chat_type=destination.chat_type.value,
        privacy_status=destination.privacy_status.value,
        bot_status=destination.bot_status.value,
        can_post=destination.can_post,
        is_active=destination.is_active,
        validation_status=destination.validation_status.value,
        last_checked_at=(
            destination.last_checked_at.isoformat()
            if destination.last_checked_at
            else None
        ),
        last_success_at=(
            destination.last_success_at.isoformat()
            if destination.last_success_at
            else None
        ),
        last_error=destination.last_error,
    )


@telegram_destinations_router.get(
    "",
    response_model=TelegramDestinationListResponse,
    dependencies=[
        Depends(require_permission(Permission.SERVICES_READ)),
    ],
)
async def list_telegram_destinations(
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=255),
    is_active: bool | None = None,
):
    query = select(TelegramDestination).order_by(
        TelegramDestination.created_at.desc()
    )
    count_query = select(func.count(TelegramDestination.id))

    if search:
        pattern = f"%{search.strip()}%"
        condition = or_(
            TelegramDestination.original_url.ilike(pattern),
            TelegramDestination.username.ilike(pattern),
            TelegramDestination.title.ilike(pattern),
        )
        query = query.where(condition)
        count_query = count_query.where(condition)

    if is_active is not None:
        query = query.where(
            TelegramDestination.is_active == is_active
        )
        count_query = count_query.where(
            TelegramDestination.is_active == is_active
        )

    total = (await session.execute(count_query)).scalar_one()

    result = await session.execute(
        query.offset((page - 1) * page_size).limit(page_size)
    )

    destinations = result.scalars().all()

    return TelegramDestinationListResponse(
        items=[
            destination_response(item)
            for item in destinations
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@telegram_destinations_router.post(
    "/import",
    dependencies=[
        Depends(require_permission(Permission.SERVICES_CREATE)),
    ],
)
async def import_telegram_destinations(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    filename = (file.filename or "").lower().strip()

    if not filename.endswith((".txt", ".csv")):
        raise HTTPException(
            status_code=400,
            detail="Only TXT and CSV files are supported.",
        )

    content = await file.read()

    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File is too large. Maximum size is 5 MB.",
        )

    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File must be UTF-8 encoded.",
        )

    rows: list[tuple[str, str | None]] = []

    if filename.endswith(".txt"):
        for line in text.splitlines():
            url = line.strip()
            if url:
                rows.append((url, None))

    else:
        reader = csv.DictReader(io.StringIO(text))

        if not reader.fieldnames:
            raise HTTPException(
                status_code=400,
                detail="CSV file has no header.",
            )

        fields = {
            field.strip().lower(): field
            for field in reader.fieldnames
            if field
        }

        url_field = fields.get("url") or fields.get("link")

        if not url_field:
            raise HTTPException(
                status_code=400,
                detail="CSV must contain a 'url' or 'link' column.",
            )

        title_field = fields.get("title") or fields.get("name")

        for row in reader:
            url = (row.get(url_field) or "").strip()
            title = (
                (row.get(title_field) or "").strip()
                if title_field
                else None
            )

            if url:
                rows.append((url, title or None))

    seen: set[str] = set()
    unique_rows: list[tuple[str, str | None]] = []

    for url, title in rows:
        key = url.rstrip("/").lower()

        if key in seen:
            continue

        seen.add(key)
        unique_rows.append((url, title))

    if not unique_rows:
        raise HTTPException(
            status_code=400,
            detail="No Telegram links were found in the file.",
        )

    urls = [url for url, _ in unique_rows]

    existing_result = await session.execute(
        select(TelegramDestination.original_url).where(
            TelegramDestination.original_url.in_(urls)
        )
    )

    existing_urls = {
        value.rstrip("/").lower()
        for value in existing_result.scalars().all()
    }

    imported = 0
    skipped_existing = 0

    for url, title in unique_rows:
        if url.rstrip("/").lower() in existing_urls:
            skipped_existing += 1
            continue

        session.add(
            TelegramDestination(
                original_url=url,
                title=title,
                is_active=True,
            )
        )
        imported += 1

    await session.commit()

    return {
        "success": True,
        "filename": file.filename,
        "total_rows": len(rows),
        "unique_links": len(unique_rows),
        "imported": imported,
        "skipped_existing": skipped_existing,
    }


@telegram_destinations_router.get(
    "/{destination_id}",
    response_model=TelegramDestinationResponse,
    dependencies=[
        Depends(require_permission(Permission.SERVICES_READ)),
    ],
)
async def get_telegram_destination(
    destination_id: UUID,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    destination = await session.get(
        TelegramDestination,
        destination_id,
    )

    if destination is None:
        raise HTTPException(
            status_code=404,
            detail="Telegram destination not found.",
        )

    return destination_response(destination)


@telegram_destinations_router.post(
    "",
    response_model=TelegramDestinationResponse,
    status_code=201,
    dependencies=[
        Depends(require_permission(Permission.SERVICES_CREATE)),
    ],
)
async def create_telegram_destination(
    payload: TelegramDestinationCreateRequest,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    original_url = payload.original_url.strip()

    if not original_url:
        raise HTTPException(
            status_code=400,
            detail="Telegram destination URL is required.",
        )

    destination = TelegramDestination(
        original_url=original_url,
        title=payload.title,
        is_active=payload.is_active,
    )

    session.add(destination)
    await session.commit()
    await session.refresh(destination)

    return destination_response(destination)


@telegram_destinations_router.patch(
    "/{destination_id}",
    response_model=TelegramDestinationResponse,
    dependencies=[
        Depends(require_permission(Permission.SERVICES_UPDATE)),
    ],
)
async def update_telegram_destination(
    destination_id: UUID,
    payload: TelegramDestinationUpdateRequest,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    destination = await session.get(
        TelegramDestination,
        destination_id,
    )

    if destination is None:
        raise HTTPException(
            status_code=404,
            detail="Telegram destination not found.",
        )

    if payload.original_url is not None:
        original_url = payload.original_url.strip()

        if not original_url:
            raise HTTPException(
                status_code=400,
                detail="Telegram destination URL cannot be empty.",
            )

        destination.original_url = original_url

    if payload.title is not None:
        destination.title = payload.title

    if payload.is_active is not None:
        destination.is_active = payload.is_active

    await session.commit()
    await session.refresh(destination)

    return destination_response(destination)
