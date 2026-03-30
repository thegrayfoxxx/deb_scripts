from collections.abc import Callable, Sequence
from dataclasses import dataclass
from importlib import import_module
from typing import Any

from app.interfaces.interactive.menu_utils import MenuItem
from app.interfaces.interactive.status_utils import status_badge

StatusRendererFactory = Callable[[Any], str]


@dataclass(frozen=True)
class ServiceRegistryEntry:
    code: str
    key: str
    name: str
    cli_label: str
    main_menu_label: str
    service_import: str
    interactive_import: str
    main_menu_status_renderer: StatusRendererFactory

    def service_factory(self) -> Any:
        return _load_attr(self.service_import)()

    def interactive_handler(self) -> None:
        _load_attr(self.interactive_import)()


def _load_attr(import_path: str) -> Any:
    module_path, attr_name = import_path.rsplit(".", 1)
    module = import_module(module_path)
    return getattr(module, attr_name)


def _ufw_status(service: Any) -> str:
    if not service.is_installed():
        return "🔴 не установлен"
    return status_badge(service.is_active(), "включен", "выключен")


def _bbr_status(service: Any) -> str:
    return status_badge(service.is_active(), "включен", "выключен")


def _docker_status(service: Any) -> str:
    return status_badge(service.is_installed(), "установлен", "не установлен")


def _fail2ban_status(service: Any) -> str:
    if not service.is_installed():
        return "🔴 не установлен"
    return status_badge(service.is_active(), "активен", "не активен")


def _traffic_guard_status(service: Any) -> str:
    if not service.is_installed():
        return "🔴 не установлен"
    return status_badge(service.is_active(), "активен", "не активен")


def _uv_status(service: Any) -> str:
    return status_badge(service.is_installed(), "установлен", "не установлен")


SERVICE_REGISTRY: tuple[ServiceRegistryEntry, ...] = (
    ServiceRegistryEntry(
        code="1",
        key="ufw",
        name="UFW",
        cli_label="1=UFW",
        main_menu_label="1 - 🔥 UFW - uncomplicated firewall (межсетевой экран)",
        service_import="app.services.ufw.UfwService",
        interactive_import="app.interfaces.interactive.ufw.interactive_run",
        main_menu_status_renderer=_ufw_status,
    ),
    ServiceRegistryEntry(
        code="2",
        key="bbr",
        name="BBR",
        cli_label="2=BBR",
        main_menu_label="2 - 🌐 BBR (TCP Congestion Control) - ускорение сети",
        service_import="app.services.bbr.BBRService",
        interactive_import="app.interfaces.interactive.bbr.interactive_run",
        main_menu_status_renderer=_bbr_status,
    ),
    ServiceRegistryEntry(
        code="3",
        key="docker",
        name="Docker",
        cli_label="3=Docker",
        main_menu_label="3 - 🐳 Docker - установка контейнеризации",
        service_import="app.services.docker.DockerService",
        interactive_import="app.interfaces.interactive.docker.interactive_run",
        main_menu_status_renderer=_docker_status,
    ),
    ServiceRegistryEntry(
        code="4",
        key="fail2ban",
        name="Fail2Ban",
        cli_label="4=Fail2Ban",
        main_menu_label="4 - 🛡️ Fail2Ban - защита от атак",
        service_import="app.services.fail2ban.Fail2BanService",
        interactive_import="app.interfaces.interactive.fail2ban.interactive_run",
        main_menu_status_renderer=_fail2ban_status,
    ),
    ServiceRegistryEntry(
        code="5",
        key="traffic_guard",
        name="TrafficGuard",
        cli_label="5=TrafficGuard",
        main_menu_label="5 - ⚔️ TrafficGuard - комплексная защита",
        service_import="app.services.traffic_guard.TrafficGuardService",
        interactive_import="app.interfaces.interactive.traffic_guard.interactive_run",
        main_menu_status_renderer=_traffic_guard_status,
    ),
    ServiceRegistryEntry(
        code="6",
        key="uv",
        name="UV",
        cli_label="6=UV",
        main_menu_label="6 - 🐍 UV - менеджер пакетов Python",
        service_import="app.services.uv.UVService",
        interactive_import="app.interfaces.interactive.uv.interactive_run",
        main_menu_status_renderer=_uv_status,
    ),
)


def get_service_registry() -> Sequence[ServiceRegistryEntry]:
    return SERVICE_REGISTRY


def get_service_entry(code: str) -> ServiceRegistryEntry | None:
    for entry in SERVICE_REGISTRY:
        if entry.code == code:
            return entry
    return None


def format_service_codes_help() -> str:
    return ", ".join(entry.cli_label for entry in SERVICE_REGISTRY)


def build_main_menu_items() -> list[MenuItem]:
    items: list[MenuItem] = []

    for entry in SERVICE_REGISTRY:
        service = entry.service_factory()
        items.append(
            MenuItem(
                key=entry.code,
                label=entry.main_menu_label,
                action=entry.interactive_handler,
                status_renderer=lambda service=service, entry=entry: (
                    entry.main_menu_status_renderer(service)
                ),
            )
        )

    return items
