"""Contracts for the future content-to-publishing pipeline."""

from dataclasses import dataclass
from enum import StrEnum


class PublishingStatus(StrEnum):
    """Lifecycle states for a future publishing job."""

    QUEUED = "queued"
    PUBLISHED = "published"
    FAILED = "failed"


@dataclass(frozen=True)
class PublishingJob:
    """A future queued publishing request."""

    job_id: str
    content_id: str
    campaign_id: str
    destination_ids: tuple[str, ...]


@dataclass(frozen=True)
class PublishingResult:
    """Result shape returned by a future publishing adapter."""

    job_id: str
    status: PublishingStatus
    successful_destination_ids: tuple[str, ...] = ()
    failed_destination_ids: tuple[str, ...] = ()
    error_message: str | None = None