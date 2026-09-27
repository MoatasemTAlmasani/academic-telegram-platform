# Environment variables

Copy `.env.example` to `.env` for local development. Never commit `.env` or
real credentials.

| Variable | Required now | Purpose |
| --- | --- | --- |
| `APP_ENV` | No | `development`, `testing`, `staging`, or `production` |
| `SECRET_KEY` | No | Reserved for future signing and security features |
| `DATABASE_URL` | No | Reserved for the PostgreSQL connection |
| `REDIS_URL` | No | Reserved for Redis-backed workers |
| `TELEGRAM_BOT_TOKEN` | No | Reserved for the future Telegram bot |
| `TELEGRAM_WEBHOOK_SECRET` | No | Reserved for future webhook verification |

None of the Phase 0 health-check code requires external services.