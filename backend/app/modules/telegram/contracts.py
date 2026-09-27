"""Contracts for future Telegram destination validation."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class DestinationType(StrEnum):
    """Telegram destination types supported by the future platform."""

    GROUP = "group"
    CHANNEL = "channel"
    UNKNOWN = "unknown"


class DestinationStatus(StrEnum):
    """Classification values for destination validation results."""

    READY = "READY"
    BOT_NOT_ADDED = "BOT_NOT_ADDED"
    NO_POST_PERMISSION = "NO_POST_PERMISSION"
    PRIVATE = "PRIVATE"
    NOT_FOUND = "NOT_FOUND"
    INVALID_LINK = "INVALID_LINK"
    DUPLICATE = "DUPLICATE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class TelegramDestination:
    """A normalized destination record awaiting validation."""

    source_link: str
    normalized_link: str | None = None
    destination_type: DestinationType = DestinationType.UNKNOWN
    status: DestinationStatus | None = None
    bot_is_member: bool | None = None
    can_post: bool | None = None


@dataclass(frozen=True)
class DestinationValidationResult:
    """Result shape a future Telegram validator must return."""

    destination: TelegramDestination
    status: DestinationStatus
    reason: str | None = None
    checked_at: str | None = None


class TelegramDestinationValidator(Protocol):
    """Interface for the future single and bulk validation engine."""

    async def validate(
        self, destination: TelegramDestination
    ) -> DestinationValidationResult:
        """Validate one destination through a future Telegram adapter."""