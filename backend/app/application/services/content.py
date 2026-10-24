"""Content application service."""

from __future__ import annotations

from uuid import UUID

from database.models.content import ContentItem, ContentTemplate

from backend.app.infrastructure.persistence.unit_of_work import UnitOfWork


class ContentService:
    """Application use cases for publishing content."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def get_by_id(
        self,
        content_id: UUID,
    ) -> ContentItem | None:
        return await self.uow.content.get_by_id(content_id)

    async def create(
        self,
        content: ContentItem,
    ) -> ContentItem:
        created = await self.uow.content.add(content)
        await self.uow.commit()
        return created

    async def create_template(
        self,
        template: ContentTemplate,
    ) -> ContentTemplate:
        created = await self.uow.content_templates.add(template)
        await self.uow.commit()
        return created

    async def get_template_by_id(
        self,
        template_id: UUID,
    ) -> ContentTemplate | None:
        return await self.uow.content_templates.get_by_id(template_id)
