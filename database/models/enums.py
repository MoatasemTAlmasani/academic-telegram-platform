"""Stable database enum values shared by domain models."""

from enum import StrEnum


class UserStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class ServiceRequestStatus(StrEnum):
    """Request lifecycle; UNDER_REVIEW is intentionally defined once."""

    NEW = "NEW"
    UNDER_REVIEW = "UNDER_REVIEW"
    WAITING_FOR_CUSTOMER = "WAITING_FOR_CUSTOMER"
    QUOTATION_SENT = "QUOTATION_SENT"
    APPROVED = "APPROVED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class RequestPriority(StrEnum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class FileScanStatus(StrEnum):
    PENDING = "PENDING"
    CLEAN = "CLEAN"
    INFECTED = "INFECTED"
    FAILED = "FAILED"


class FileAccessStatus(StrEnum):
    PRIVATE = "PRIVATE"
    SHARED = "SHARED"
    RESTRICTED = "RESTRICTED"


class QuoteStatus(StrEnum):
    DRAFT = "DRAFT"
    SENT = "SENT"
    ACCEPTED = "ACCEPTED"
    CHANGE_REQUESTED = "CHANGE_REQUESTED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class TelegramChatType(StrEnum):
    GROUP = "GROUP"
    SUPERGROUP = "SUPERGROUP"
    CHANNEL = "CHANNEL"
    UNKNOWN = "UNKNOWN"


class TelegramPrivacyStatus(StrEnum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"
    UNKNOWN = "UNKNOWN"


class TelegramBotStatus(StrEnum):
    ADDED = "ADDED"
    NOT_ADDED = "NOT_ADDED"
    UNKNOWN = "UNKNOWN"


class TelegramValidationStatus(StrEnum):
    IMPORTED = "IMPORTED"
    JOINING = "JOINING"
    JOINED = "JOINED"
    JOIN_REQUEST_PENDING = "JOIN_REQUEST_PENDING"
    JOIN_FAILED = "JOIN_FAILED"
    READY = "READY"
    BOT_NOT_ADDED = "BOT_NOT_ADDED"
    NO_POST_PERMISSION = "NO_POST_PERMISSION"
    PRIVATE = "PRIVATE"
    NOT_FOUND = "NOT_FOUND"
    INVALID_LINK = "INVALID_LINK"
    DUPLICATE = "DUPLICATE"
    ERROR = "ERROR"


class ContentType(StrEnum):
    TEXT = "TEXT"
    MEDIA = "MEDIA"
    ANNOUNCEMENT = "ANNOUNCEMENT"


class ContentStatus(StrEnum):
    DRAFT = "DRAFT"
    READY = "READY"
    ARCHIVED = "ARCHIVED"


class CampaignStatus(StrEnum):
    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class PublishingStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    SKIPPED = "SKIPPED"