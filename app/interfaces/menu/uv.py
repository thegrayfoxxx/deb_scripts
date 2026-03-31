from app.interfaces.menu.menu_utils import (
    build_standard_service_menu_items,
    prompt_service_submenu,
    return_to_main_menu,
    run_menu_loop,
    show_info_screen,
)
from app.services.uv import UVService


def _build_menu_items(service: UVService):
    return build_standard_service_menu_items(
        service=service,
        primary_key="1",
        primary_label="1 - 📦 Установить UV",
        primary_action=service.install,
        primary_is_ok=service.is_installed,
        primary_ok_text="установлен",
        primary_fail_text="не установлен",
        uninstall_key="2",
        uninstall_label="2 - 🗑️ Удалить UV",
        uninstall_action=lambda: service.uninstall(confirm=True),
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
    show_info_screen("🐍 UV", UVService().get_info_lines())


def interactive_run():
    service = UVService()

    run_menu_loop(
        title="🐍 Управление UV",
        header="Доступные действия для UV:",
        items_factory=lambda: _build_menu_items(service),
        info_handler=display_uv_info,
        exit_handler=return_to_main_menu,
        info_label="00 - ℹ️ Информация о UV",
        exit_label="0 - 🏠 Вернуться в главное меню",
    )
