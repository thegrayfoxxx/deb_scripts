from app.interfaces.interactive.menu_utils import (
    build_standard_service_menu_items,
    prompt_service_submenu,
    return_to_main_menu,
    run_menu_loop,
    show_info_screen,
)
from app.services.traffic_guard import TrafficGuardService


def _build_menu_items(service: TrafficGuardService):
    return build_standard_service_menu_items(
        service=service,
        primary_key="1",
        primary_label="1 - 🔒 Установить TrafficGuard",
        primary_action=service.install,
        primary_is_ok=service.is_installed,
        primary_ok_text="установлен",
        primary_fail_text="не установлен",
        uninstall_key="2",
        uninstall_label="2 - 🔓 Удалить TrafficGuard",
        uninstall_action=lambda: service.uninstall(confirm=True),
        status_key="3",
        status_label="3 - 📊 Показать статус TrafficGuard",
    )


def display_trafficguard_submenu(service: TrafficGuardService):
    """Отображает подменю для TrafficGuard с выбором действий"""
    return prompt_service_submenu(
        header="Доступные действия для TrafficGuard:",
        items=_build_menu_items(service),
        info_label="00 - ℹ️ Информация о TrafficGuard",
    )


def display_trafficguard_info():
    """Отображает информацию о TrafficGuard сервисе"""
    show_info_screen("⚔️ TrafficGuard Server Protection", TrafficGuardService().get_info_lines())


def interactive_run():
    service = TrafficGuardService()

    run_menu_loop(
        title="⚔️ TrafficGuard Server Protection",
        header="Доступные действия для TrafficGuard:",
        items_factory=lambda: _build_menu_items(service),
        info_handler=display_trafficguard_info,
        exit_handler=return_to_main_menu,
        info_label="00 - ℹ️ Информация о TrafficGuard",
        exit_label="0 - 🏠 Вернуться в главное меню",
    )
