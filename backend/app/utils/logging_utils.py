import logging
import os
from datetime import datetime


LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_LEVEL = os.getenv("RHYME_LOG_LEVEL", "INFO").upper()
LOG_TO_FILE = os.getenv("RHYME_LOG_TO_FILE", "false").lower() == "true"

_logger: logging.Logger | None = None


def setup_logging() -> logging.Logger:
    global _logger
    if _logger is not None:
        return _logger

    logger = logging.getLogger("rhyme")
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    if logger.handlers:
        _logger = logger
        return logger

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if LOG_TO_FILE:
        log_filename = datetime.now().strftime("rhyme_%Y-%m-%d.log")
        file_handler = logging.FileHandler(os.path.join(LOG_DIR, log_filename), encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    _logger = logger
    return logger
