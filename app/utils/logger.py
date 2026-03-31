import logging
import sys
from pathlib import Path

LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}
DEFAULT_CONSOLE_LEVEL = logging.INFO
STREAM_HANDLER_CLASS = logging.StreamHandler
FILE_HANDLER_CLASS = logging.FileHandler


def _resolve_console_level(level: int | str | None = None) -> int:
    if isinstance(level, int):
        return level
    if isinstance(level, str):
        return LOG_LEVELS[level.lower()]
    return DEFAULT_CONSOLE_LEVEL


def set_default_console_level(level: int | str) -> None:
    """Обновляет уровень консольного логирования для новых и существующих логгеров."""
    global DEFAULT_CONSOLE_LEVEL
    DEFAULT_CONSOLE_LEVEL = _resolve_console_level(level)

    for logger in logging.root.manager.loggerDict.values():
        if not isinstance(logger, logging.Logger):
            continue
        for handler in logger.handlers:
            if isinstance(handler, STREAM_HANDLER_CLASS) and not isinstance(
                handler, FILE_HANDLER_CLASS
            ):
                handler.setLevel(DEFAULT_CONSOLE_LEVEL)


def get_logger(
    name: str, log_file: str = "app.log", level: int | str | None = None
) -> logging.Logger:
    """Create a logger with concise console output and verbose file logging."""
    console_level = _resolve_console_level(level)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    if logger.handlers:
        for handler in logger.handlers:
            if isinstance(handler, STREAM_HANDLER_CLASS) and not isinstance(
                handler, FILE_HANDLER_CLASS
            ):
                handler.setLevel(console_level)
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
