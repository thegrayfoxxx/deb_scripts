import os


def check_root() -> None:
    """Проверка прав суперпользователя"""
    if os.geteuid() != 0:
        raise PermissionError("Скрипт требует прав root (sudo)")
