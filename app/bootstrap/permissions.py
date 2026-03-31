import os

from app.i18n.locale import t


def check_root() -> None:
    """Проверка прав суперпользователя"""
    if os.geteuid() != 0:
        raise PermissionError(t("common.root_required"))
