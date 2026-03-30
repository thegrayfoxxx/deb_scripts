import logging
import sys
from pathlib import Path

from app.utils.args_utils import app_args

LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}


def _resolve_console_level(level: int | str | None = None) -> int:
    if isinstance(level, int):
        return level
    if isinstance(level, str):
        return LOG_LEVELS[level.lower()]

    configured_level = getattr(app_args, "log_level", None)
    if configured_level in LOG_LEVELS:
        return LOG_LEVELS[configured_level]

    mode = getattr(app_args, "mode", "prod")
    return logging.DEBUG if mode == "dev" else logging.INFO


def get_logger(
    name: str, log_file: str = "app.log", level: int | str | None = None
) -> logging.Logger:
    """Create a logger with concise console output and verbose file logging."""
    console_level = _resolve_console_level(level)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    if logger.handlers:
        return logger

    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    file_formatter = logging.Formatter(log_format, datefmt=date_format)
    console_formatter = logging.Formatter("%(message)s")

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(console_level)
    logger.addHandler(console_handler)

    try:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, encoding="utf-8", mode="a")
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
    except OSError:
        pass

    return logger
