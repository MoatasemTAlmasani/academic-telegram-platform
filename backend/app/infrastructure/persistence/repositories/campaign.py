"""Campaign repository."""

from database.models.campaigns import Campaign

from .base import BaseRepository


class CampaignRepository(BaseRepository[Campaign]):
    """Persistence operations for campaigns."""

    model = Campaign
