import logging
import os
from logging.handlers import TimedRotatingFileHandler


def configure_basic_logging():
    """Configure process-wide logging once with env override support."""
    level_name = (os.getenv("RHYME_LOG_LEVEL", "INFO") or "INFO").strip().upper()
    level = getattr(logging, level_name, logging.INFO)

    root_logger = logging.getLogger()
    formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")

    if root_logger.handlers:
        root_logger.setLevel(level)
        for handler in root_logger.handlers:
            handler.setLevel(level)
        return

    root_logger.setLevel(level)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    log_to_file = (os.getenv("RHYME_LOG_TO_FILE", "false") or "false").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    if not log_to_file:
        return

    log_dir = (os.getenv("RHYME_LOG_DIR", "") or "").strip() or os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "rhyme.log")

    backup_count_raw = (os.getenv("RHYME_LOG_BACKUP_DAYS", "7") or "7").strip()
    try:
        backup_count = max(1, int(backup_count_raw))
    except Exception:
        backup_count = 7

    file_handler = TimedRotatingFileHandler(
        log_path,
        when="midnight",
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)


def get_logger(name):
    return logging.getLogger(name)


