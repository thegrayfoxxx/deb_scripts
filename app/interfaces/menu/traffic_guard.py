from app.i18n.locale import t
from app.interfaces.menu.menu_utils import (
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
        primary_label=t("menu.standard.install_service", code="1", service="TrafficGuard"),
        primary_action=service.install,
        primary_is_ok=service.is_installed,
        primary_ok_text=t("common.installed"),
        primary_fail_text=t("common.not_installed"),
        uninstall_key="2",
        uninstall_label=t("menu.standard.uninstall_service", code="2", service="TrafficGuard"),
        uninstall_action=lambda: service.uninstall(confirm=True),
        status_key="3",
        status_label=t("menu.standard.show_status", code="3", service="TrafficGuard"),
    )


def display_trafficguard_submenu(service: TrafficGuardService):
    """Отображает подменю для TrafficGuard с выбором действий"""
    return prompt_service_submenu(
        header=t("menu.standard.service_header", service="TrafficGuard"),
        items=_build_menu_items(service),
        info_label=t("menu.standard.info_about_service", service="TrafficGuard"),
    )


def display_trafficguard_info():
    """Отображает информацию о TrafficGuard сервисе"""
    show_info_screen("⚔️ TrafficGuard", TrafficGuardService().get_info_lines())


def interactive_run():
    service = TrafficGuardService()

    run_menu_loop(
        title=t("menu.standard.manage_service", icon="⚔️", service="TrafficGuard"),
        header=t("menu.standard.service_header", service="TrafficGuard"),
        items_factory=lambda: _build_menu_items(service),
        info_handler=display_trafficguard_info,
        exit_handler=return_to_main_menu,
        info_label=t("menu.standard.info_about_service", service="TrafficGuard"),
        exit_label=t("menu.service_exit_label"),
    )
