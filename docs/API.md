# API

## Versioning

New public API routes belong under `/api/v1/`. A future `/api/v2/` can be
introduced without changing existing clients.

## Current endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Operational liveness check |
| `GET` | `/health/ready` | Readiness shape for future dependency checks |
| `GET` | `/api/v1/health` | Versioned liveness check |
| `GET` | `/api/v1/health/ready` | Versioned readiness check |

Readiness currently reports configured external services as `not_checked`; it
does not claim a service is available until a later phase adds real dependency
checks.

## Response conventions

Successful responses expose `success: true`. Errors use the following shape:

```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Resource not found"
  }
}
```

Validation errors may also include a `details` array. Internal exceptions are
logged server-side and return `INTERNAL_SERVER_ERROR` without exposing
implementation details.