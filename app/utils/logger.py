import logging
import sys
from pathlib import Path

from app.utils.args_utils import app_args


def get_logger(name: str, log_file: str = "app.log", level: int = logging.INFO) -> logging.Logger:
    """
    Настраивает и возвращает стандартный логгер.
    """
    # Переопределяем уровень для режима разработки
    if app_args.mode == "dev":
        level = logging.DEBUG

    logger = logging.getLogger(name)

    # ✅ ВАЖНО: Устанавливаем уровень самого логгера
    logger.setLevel(level)

    # ✅ Защита от дублирования обработчиков при повторных вызовах
    if logger.handlers:
        return logger

    # Формат для файла: время, имя, уровень, сообщение
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    file_formatter = logging.Formatter(log_format, datefmt=date_format)

    # Формат для консоли: только сообщение (чище для интерактива)
    console_formatter = logging.Formatter("%(message)s")

    # 1. Обработчик для КОНСОЛИ
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(level)
    logger.addHandler(console_handler)

    # 2. Обработчик для ФАЙЛА
    # Создаём директорию для логов, если не существует
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(log_path, encoding="utf-8", mode="a")
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(level)
    logger.addHandler(file_handler)

    return logger
