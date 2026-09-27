"""Run the FastAPI application locally."""

import os

import uvicorn


def main() -> None:
    """Start the development server using environment-provided settings."""
    uvicorn.run(
        "backend.app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("APP_ENV", "development") == "development",
    )


if __name__ == "__main__":
    main()