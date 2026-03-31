from app.bootstrap.logger import get_logger
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
from app.services.ufw import UfwService

logger = get_logger(__name__)

PortGroupEntry = dict[str, str | list[str]]

PORT_GROUPS = {
    "1": {
        "name_key": "menu.ufw.port_group.ssh_name",
        "ports": ["22"],
        "desc_key": "menu.ufw.port_group.ssh_desc",
    },
    "2": {
        "name_key": "menu.ufw.port_group.web_name",
        "ports": ["80", "443"],
        "desc_key": "menu.ufw.port_group.web_desc",
    },
    "3": {
        "name_key": "menu.ufw.port_group.dns_name",
        "ports": ["53"],
        "desc_key": "menu.ufw.port_group.dns_desc",
    },
    "4": {
        "name_key": "menu.ufw.port_group.dhcp_name",
        "ports": ["67", "68"],
        "desc_key": "menu.ufw.port_group.dhcp_desc",
    },
    "5": {
        "name_key": "menu.ufw.port_group.mail_name",
        "ports": ["25", "587", "465", "143", "993", "110", "995"],
        "desc_key": "menu.ufw.port_group.mail_desc",
    },
    "6": {
        "name_key": "menu.ufw.port_group.ftp_name",
        "ports": ["20", "21"],
        "desc_key": "menu.ufw.port_group.ftp_desc",
    },
    "7": {
        "name_key": "menu.ufw.port_group.remnawave_name",
        "ports": ["2222"],
        "desc_key": "menu.ufw.port_group.remnawave_desc",
    },
    "8": {
        "name_key": "menu.ufw.port_group.mysql_name",
        "ports": ["3306"],
        "desc_key": "menu.ufw.port_group.mysql_desc",
    },
    "9": {
        "name_key": "menu.ufw.port_group.postgres_name",
        "ports": ["5432"],
        "desc_key": "menu.ufw.port_group.postgres_desc",
    },
    "10": {
        "name_key": "menu.ufw.port_group.all_name",
        "ports": [],
        "desc_key": "menu.ufw.port_group.all_desc",
    },
}


def _install_status(service: UfwService) -> str:
    return installation_status_badge(service.is_installed())


def _active_status(service: UfwService) -> str:
    if not service.is_installed():
        return installation_status_badge(False)
    return activation_status_badge(service.is_active())


def _build_menu_items(service: UfwService) -> list[MenuItem]:
    install_status = _install_status(service)
    active_status = _active_status(service)

    return [
        MenuItem(
            key="1",
            label=t("menu.ufw.install"),
            action=service.install,
            status_renderer=lambda status=install_status: status,
        ),
        MenuItem(
            key="2",
            label=t("menu.ufw.activate"),
            action=service.activate,
            status_renderer=lambda status=active_status: status,
        ),
        MenuItem(
            key="3",
            label=t("menu.ufw.open_list"),
            action=lambda: _open_specific_ports(service),
        ),
        MenuItem(
            key="4",
            label=t("menu.ufw.close_list"),
            action=lambda: _close_specific_ports(service),
        ),
        MenuItem(
            key="5",
            label=t("menu.ufw.open_custom"),
            action=lambda: _manage_custom_port(service, action="open"),
        ),
        MenuItem(
            key="6",
            label=t("menu.ufw.close_custom"),
            action=lambda: _manage_custom_port(service, action="close"),
        ),
        MenuItem(
            key="7",
            label=t("menu.ufw.status"),
            action=lambda: print(service.get_status()),
        ),
        MenuItem(
            key="8",
            label=t("menu.ufw.deactivate"),
            action=lambda: service.deactivate(confirm=True),
        ),
        MenuItem(
            key="9",
            label=t("menu.ufw.reset"),
            action=lambda: service.reset(confirm=True),
        ),
        MenuItem(
            key="10",
            label=t("menu.ufw.uninstall"),
            action=lambda: service.uninstall(confirm=True),
        ),
    ]


def display_ufw_submenu(service: UfwService) -> str:
    """Отображает подменю UFW и возвращает выбор пользователя."""
    return prompt_service_submenu(
        header=t("common.select_action"),
        items=_build_menu_items(service),
        info_label=t("menu.standard.info_about_service", service="UFW"),
    )


def _collect_ports_from_group_selection(*, include_ssh: bool) -> list[str]:
    for key, value in PORT_GROUPS.items():
        if not include_ssh and key == "1":
            continue
        name_key = str(value["name_key"])
        desc_key = str(value["desc_key"])
        print(f"{key} - {t(name_key)}: {t(desc_key)}")
    print(f"0 - {t('common.cancel')}")

    choice = input(t("menu.ufw.group.enter_numbers")).strip().split()
    if "0" in choice:
        return []

    selected_ports: set[str] = set()
    for option in choice:
        if option == "10":
            for group_key, value in PORT_GROUPS.items():
                if group_key not in {"1", "10"}:
                    selected_ports.update(value["ports"])
        elif option in PORT_GROUPS and option != "1":
            selected_ports.update(PORT_GROUPS[option]["ports"])

    return sorted(selected_ports)


def _apply_ports(service: UfwService, ports: list[str], *, action: str) -> None:
    if not ports:
        print(t("menu.ufw.no_ports_selected"))
        return

    service_action = service.open_port if action == "open" else service.close_port

    message_key = (
        "menu.ufw.action.opening_ports" if action == "open" else "menu.ufw.action.closing_ports"
    )
    print(f"\n{t(message_key, ports=', '.join(ports))}")
    success_count = 0
    for port in ports:
        if service_action(port):
            print(
                t(
                    "menu.ufw.port_opened" if action == "open" else "menu.ufw.port_closed",
                    port=port,
                )
            )
            success_count += 1
        else:
            print(
                t(
                    "menu.ufw.port_open_failed"
                    if action == "open"
                    else "menu.ufw.port_close_failed",
                    port=port,
                )
            )

    if success_count > 0:
        print(t("menu.ufw.ports_processed", count=success_count))
    else:
        print(t("menu.ufw.no_ports_processed"))


def _open_specific_ports(service):
    """Интерактивное открытие конкретных портов."""
    print(t("menu.ufw.group.select_open"))
    _apply_ports(service, _collect_ports_from_group_selection(include_ssh=True), action="open")


def _close_specific_ports(service):
    """Интерактивное закрытие конкретных портов из готового списка."""
    print(t("menu.ufw.group.select_close"))
    print(t("menu.ufw.group.ssh_hidden"))
    _apply_ports(service, _collect_ports_from_group_selection(include_ssh=False), action="close")


def _manage_custom_port(service: UfwService, *, action: str) -> None:
    port = input(t("menu.ufw.custom_port_prompt")).strip()
    if not port:
        print(t("menu.ufw.port_not_specified"))
        return

    if action == "close" and port.lower() in UfwService.SSH_PORT_ALIASES:
        print(t("menu.ufw.ssh_rule_cannot_be_removed"))
        return

    service_action = service.open_port if action == "open" else service.close_port
    success = service_action(port)
    if success:
        print(t("menu.ufw.port_opened" if action == "open" else "menu.ufw.port_closed", port=port))
    else:
        print(
            t(
                "menu.ufw.port_open_failed" if action == "open" else "menu.ufw.port_close_failed",
                port=port,
            )
        )


def display_ufw_info():
    """Отображает информацию о UFW сервисе"""
    show_info_screen("🔥 UFW", UfwService().get_info_lines())


def interactive_run():
    """Entry point for UFW interactive mode."""
    service = UfwService()

    run_menu_loop(
        title=t("menu.standard.manage_service", icon="🔥", service="UFW"),
        header=t("common.select_action"),
        items_factory=lambda: _build_menu_items(service),
        info_handler=display_ufw_info,
        exit_handler=return_to_main_menu,
        info_label=t("menu.standard.info_about_service", service="UFW"),
        exit_label=t("menu.service_exit_label"),
        intro_lines=[t("menu.ufw.safe_baseline_hint")],
        invalid_message=t("common.invalid_option"),
    )
