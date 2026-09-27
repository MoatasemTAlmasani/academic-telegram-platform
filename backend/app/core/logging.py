"""Logging configuration shared by the application and future workers."""

import logging


def configure_logging() -> None:
    """Configure readable application logs once at process startup."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )