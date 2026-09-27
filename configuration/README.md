# Configuration

Runtime configuration is defined in `backend/app/core/config.py` and loaded
from environment variables. It currently covers `APP_ENV`, `DEBUG`,
`SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`, `TELEGRAM_BOT_TOKEN`, and
`TELEGRAM_WEBHOOK_SECRET`.

Keep local values in `.env`, which is ignored by Git; commit only
`.env.example`.