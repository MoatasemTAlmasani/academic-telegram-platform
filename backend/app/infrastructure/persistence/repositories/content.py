"""Content repositories."""

from database.models.content import ContentItem, ContentTemplate

from .base import BaseRepository


class ContentRepository(BaseRepository[ContentItem]):
    """Persistence operations for content items."""

    model = ContentItem


class ContentTemplateRepository(BaseRepository[ContentTemplate]):
    """Persistence operations for content templates."""

    model = ContentTemplate
