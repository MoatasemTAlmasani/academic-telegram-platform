# Development guide

## Prerequisites

- Python 3.11 or newer
- `uv` (recommended) or another tool that can install from `pyproject.toml`

## Install

```bash
uv sync
```

## Run the API

```bash
uv run python -m backend
```

The server listens on `PORT` when provided, otherwise port `8000`.

## Run tests

```bash
uv run pytest
```

## Check the health endpoint

```bash
curl http://localhost:8000/health
```