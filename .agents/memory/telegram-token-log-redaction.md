---
name: Telegram token log redaction
description: Prevent Telegram bot credentials from leaking through request logs and exception traces.
---

Telegram Bot API credentials are embedded in request URL paths. HTTP client INFO logs and HTTP status exception traces can both include the full URL, so suppressing request INFO logs alone is not sufficient.

**Why:** A polling conflict produced an HTTP status traceback that included its Telegram request URL even after normal HTTP client INFO logging was disabled.

**How to apply:** Redact Telegram Bot API URL credentials in both structured log messages and formatted exceptions, and test both paths without printing real credentials.
