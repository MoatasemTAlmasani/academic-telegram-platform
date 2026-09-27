# Telegram architecture

The Telegram subsystem is isolated under `backend/app/modules/telegram/` and
the future `bot/` package. The application layer will depend on
`TelegramService` and destination validation contracts instead of importing
aiogram clients directly.

## Future destination flow

```text
Input links
  → normalization
  → duplicate detection
  → destination type detection
  → bot membership check
  → permission check
  → status classification
  → validation log
  → revalidation
```

Supported future statuses are `READY`, `BOT_NOT_ADDED`, `NO_POST_PERMISSION`,
`PRIVATE`, `NOT_FOUND`, `INVALID_LINK`, `DUPLICATE`, and `ERROR`.

Phase 1 defines the destination and validation result contracts only. It does
not import links, contact Telegram, join destinations, validate permissions,
or run bot handlers.

The future publishing path is:

```text
Content
  → Campaign
  → Destination Selection
  → Scheduler
  → Publishing Queue
  → Telegram API
  → Success / Failure
  → Logs
```

The bot must only operate on destinations where it has been legitimately added
and has the required permissions.