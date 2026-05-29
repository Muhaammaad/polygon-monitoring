import logging
from typing import Optional

from core.config import get_config
from .json_formatter import JsonFormatter


# Logging setup function
def configure_logging(level: Optional[str] = None) -> None:
    """Configure root logger based on app config.

    Uses JSON formatter when LOG_FORMAT or config.logging.format == 'json'.
    """
    cfg = get_config().get_logging_config()
    fmt = (cfg.get('format') or 'json').lower()
    lvl = (level or cfg.get('level') or 'INFO').upper()

    root = logging.getLogger()
    root.setLevel(getattr(logging, lvl, logging.INFO))

    # Clear existing handlers to avoid duplicates
    root.handlers = []

    handler = logging.StreamHandler()
    if fmt == 'json':
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s - %(message)s'))

    # Add handler to root logger
    root.addHandler(handler)
