# Configuration

Runtime configuration is defined in `backend/app/core/config.py` and loaded
from environment variables. It currently covers `APP_ENV`, `DEBUG`,
`SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`, `TELEGRAM_BOT_TOKEN`, and
`TELEGRAM_WEBHOOK_SECRET`, and the optional SMTP settings used for verified email delivery.

Keep local values in `.env`, which is ignored by Git; commit only
`.env.example`.

## Verified email delivery

Set these environment variables in the deployment platform (never commit their values):

- `EMAIL_SMTP_HOST`
- `EMAIL_SMTP_PORT` (default: `587`)
- `EMAIL_SMTP_USERNAME` and `EMAIL_SMTP_PASSWORD` (set both or neither)
- `EMAIL_SMTP_FROM`
- `EMAIL_SMTP_STARTTLS` (default: `true`)
- `EMAIL_SMTP_USE_SSL` (default: `false`; use implicit TLS when enabled)
- `PUBLIC_APP_URL` (default: `https://ehteraf-tech.vercel.app`; used to build email verification links)

Email recovery and email ownership verification remain unavailable until a working SMTP host and sender are configured. If authentication is used, both username and password must be set. Do not place SMTP credentials in source control or client-side code.
