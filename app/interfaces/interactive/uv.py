from app.interfaces.interactive.menu_utils import (
    build_standard_service_menu_items,
    prompt_service_submenu,
    return_to_main_menu,
    run_menu_loop,
    show_info_screen,
)
from app.services.uv import UVService

INFO_LINES = [
    "UV — современный и быстрый менеджер пакетов Python",
    "Основные преимущества:",
    "• Высокая скорость установки пакетов (в 10-100 раз быстрее, чем pip)",
    "• Современная система разрешения зависимостей",
    "• Альтернатива для pip, pipenv, poetry и других",
    "• Надежная изоляция окружений",
    "• Улучшенная безопасность при установке пакетов",
    "• Полная совместимость с PyPI и системой пакетов Python",
    "🔗 GitHub репозиторий: https://github.com/astral-sh/uv",
    "🔗 Официальный сайт: https://astral.sh",
]


def _build_menu_items(service: UVService):
    return build_standard_service_menu_items(
        service=service,
        primary_key="1",
        primary_label="1 - 📦 Установить UV",
        primary_action=service.install_uv,
        primary_is_ok=service.is_installed,
        primary_ok_text="установлен",
        primary_fail_text="не установлен",
        uninstall_key="2",
        uninstall_label="2 - 🗑️ Удалить UV",
        uninstall_action=lambda: service.uninstall_uv(confirm=True),
        status_key="3",
        status_label="3 - 📊 Показать статус UV",
    )


def display_uv_submenu(service: UVService):
    """Отображает подменю для UV с выбором действий"""
    return prompt_service_submenu(
        header="Доступные действия для UV:",
        items=_build_menu_items(service),
        info_label="00 - ℹ️ Информация о UV",
    )


def display_uv_info():
    """Отображает информацию о UV сервисе"""
    show_info_screen("🐍 UV Python Package Manager", INFO_LINES)


def interactive_run():
    service = UVService()

    run_menu_loop(
        title="🐍 UV Python Package Manager",
        header="Доступные действия для UV:",
        items=_build_menu_items(service),
        info_handler=display_uv_info,
        exit_handler=return_to_main_menu,
        info_label="00 - ℹ️ Информация о UV",
        exit_label="0 - 🏠 Вернуться в главное меню",
    )
