"""Campaign application service."""

from __future__ import annotations

from uuid import UUID

from database.models.campaigns import Campaign

from backend.app.infrastructure.persistence.unit_of_work import UnitOfWork


class CampaignService:
    """Application use cases for campaigns."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def get_by_id(
        self,
        campaign_id: UUID,
    ) -> Campaign | None:
        return await self.uow.campaigns.get_by_id(campaign_id)

    async def create(self, campaign: Campaign) -> Campaign:
        created = await self.uow.campaigns.add(campaign)
        await self.uow.commit()
        return created
