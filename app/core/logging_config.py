from utils import adhanLogger  # noqa: F401 - side-effect sets up logging handlers
import logging


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger using existing utils/adhanLogger setup."""
    return logging.getLogger(name)

