"""Contracts for future bulk Telegram destination imports."""

from dataclasses import dataclass

from backend.app.modules.telegram.contracts import (
    DestinationStatus,
    TelegramDestination,
)


@dataclass(frozen=True)
class DestinationImportBatch:
    """Raw links submitted for a future bulk import operation."""

    source_links: tuple[str, ...]


@dataclass(frozen=True)
class DestinationImportResult:
    """Result shape for a future import and classification operation."""

    destinations: tuple[TelegramDestination, ...]
    duplicate_links: tuple[str, ...] = ()
    rejected_links: tuple[tuple[str, DestinationStatus], ...] = ()