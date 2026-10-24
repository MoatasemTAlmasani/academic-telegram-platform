"""Service catalog repository."""

from database.models.catalog import Service

from .base import BaseRepository


class ServiceRepository(BaseRepository[Service]):
    """Persistence operations for academic services."""

    model = Service
