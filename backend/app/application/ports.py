"""Interfaces for infrastructure-backed application services."""

from collections.abc import Awaitable
from dataclasses import dataclass
from typing import Protocol

from backend.app.modules.publishing.contracts import PublishingJob, PublishingResult
from backend.app.modules.telegram.contracts import (
    DestinationValidationResult,
    TelegramDestination,
)


@dataclass(frozen=True)
class StoredFile:
    """Metadata returned by a future storage adapter."""

    file_id: str
    filename: str
    content_type: str


class TelegramService(Protocol):
    """Boundary for Telegram API and destination operations."""

    def validate_destination(
        self, destination: TelegramDestination
    ) -> Awaitable[DestinationValidationResult]:
        """Validate a destination through a future Telegram adapter."""


class StorageService(Protocol):
    """Boundary for secure file storage."""

    def store(
        self,
        *,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> Awaitable[StoredFile]:
        """Store a file through a future storage adapter."""


class NotificationService(Protocol):
    """Boundary for email, Telegram, or in-app notifications."""

    def notify(self, *, recipient_id: str, message: str) -> Awaitable[None]:
        """Deliver a notification through a future adapter."""


class PublishingService(Protocol):
    """Boundary for the future publishing pipeline."""

    def publish(self, job: PublishingJob) -> Awaitable[PublishingResult]:
        """Publish a queued job through a future Telegram adapter."""