# Development

## Install

```bash
uv sync --dev
```

The optional infrastructure dependencies can be installed later with:

```bash
uv sync --dev --extra infra
```

## Run

```bash
uv run python -m backend
```

The server listens on `PORT` when provided, otherwise port `8000`.

## Test and checks

```bash
uv run pytest
pnpm run typecheck
```

## Health checks

```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/ready
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/health/ready
```