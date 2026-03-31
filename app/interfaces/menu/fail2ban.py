from app.core.status import (
    activation_status_badge,
    installation_status_badge,
)
from app.i18n.locale import t
from app.interfaces.menu.menu_utils import (
    MenuItem,
    prompt_service_submenu,
    return_to_main_menu,
    run_menu_loop,
    show_info_screen,
)
from app.services.fail2ban import Fail2BanService


def _build_menu_items(service: Fail2BanService):
    install_status = installation_status_badge(service.is_installed())
    activation_status = activation_status_badge(service.is_active())

    return [
        MenuItem(
            key="1",
            label=t("menu.fail2ban.install"),
            action=service.install,
            status_renderer=lambda status=install_status: status,
        ),
        MenuItem(
            key="2",
            label=t("menu.fail2ban.activate"),
            action=service.activate,
            status_renderer=lambda status=activation_status: status,
        ),
        MenuItem(
            key="3",
            label=t("menu.fail2ban.deactivate"),
            action=lambda: service.deactivate(confirm=True),
        ),
        MenuItem(
            key="4",
            label=t("menu.fail2ban.uninstall"),
            action=lambda: service.uninstall(confirm=True),
        ),
        MenuItem(
            key="5",
            label=t("menu.fail2ban.status"),
            action=lambda: print(service.get_status()),
        ),
    ]


def display_fail2ban_submenu(service: Fail2BanService):
    """Отображает подменю для Fail2Ban с выбором действий"""
    return prompt_service_submenu(
        header=t("menu.standard.service_header", service="Fail2Ban"),
        items=_build_menu_items(service),
        info_label=t("menu.standard.info_about_service", service="Fail2Ban"),
    )


def display_fail2ban_info():
    """Отображает информацию о Fail2Ban сервисе"""
    show_info_screen("🛡️ Fail2Ban", Fail2BanService().get_info_lines())


def interactive_run():
    service = Fail2BanService()

    run_menu_loop(
        title=t("menu.standard.manage_service", icon="🛡️", service="Fail2Ban"),
        header=t("menu.standard.service_header", service="Fail2Ban"),
        items_factory=lambda: _build_menu_items(service),
        info_handler=display_fail2ban_info,
        exit_handler=return_to_main_menu,
        info_label=t("menu.standard.info_about_service", service="Fail2Ban"),
        exit_label=t("menu.service_exit_label"),
    )
