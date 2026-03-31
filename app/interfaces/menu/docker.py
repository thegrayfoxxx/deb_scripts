from app.i18n.locale import t
from app.interfaces.menu.menu_utils import (
    build_standard_service_menu_items,
    prompt_service_submenu,
    return_to_main_menu,
    run_menu_loop,
    show_info_screen,
)
from app.services.docker import DockerService


def _build_menu_items(service: DockerService):
    return build_standard_service_menu_items(
        service=service,
        primary_key="1",
        primary_label=t("menu.standard.install_service", code="1", service="Docker"),
        primary_action=service.install,
        primary_is_ok=service.is_installed,
        primary_ok_text=t("common.installed"),
        primary_fail_text=t("common.not_installed"),
        uninstall_key="2",
        uninstall_label=t("menu.standard.uninstall_service", code="2", service="Docker"),
        uninstall_action=lambda: service.uninstall(confirm=True),
        status_key="3",
        status_label=t("menu.standard.show_status", code="3", service="Docker"),
    )


def display_docker_submenu(service: DockerService):
    """Отображает подменю для Docker с выбором действий"""
    return prompt_service_submenu(
        header=t("menu.standard.service_header", service="Docker"),
        items=_build_menu_items(service),
        info_label=t("menu.standard.info_about_service", service="Docker"),
    )


def display_docker_info():
    """Отображает информацию о Docker сервисе"""
    show_info_screen("🐳 Docker", DockerService().get_info_lines())


def interactive_run():
    service = DockerService()

    run_menu_loop(
        title=t("menu.standard.manage_service", icon="🐳", service="Docker"),
        header=t("menu.standard.service_header", service="Docker"),
        items_factory=lambda: _build_menu_items(service),
        info_handler=display_docker_info,
        exit_handler=return_to_main_menu,
        info_label=t("menu.standard.info_about_service", service="Docker"),
        exit_label=t("menu.service_exit_label"),
    )
