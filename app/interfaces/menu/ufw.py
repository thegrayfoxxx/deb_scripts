from app.bootstrap.logger import get_logger
from app.core.status import (
    activation_status_badge,
    installation_status_badge,
)
from app.interfaces.menu.menu_utils import (
    MenuItem,
    prompt_service_submenu,
    return_to_main_menu,
    run_menu_loop,
    show_info_screen,
)
from app.services.ufw import UfwService

logger = get_logger(__name__)

PORT_GROUPS = {
    "1": {"name": "SSH", "ports": ["22"], "desc": "SSH (22, всегда разрешён)"},
    "2": {
        "name": "Web-сервер",
        "ports": ["80", "443"],
        "desc": "HTTP и HTTPS (80, 443)",
    },
    "3": {"name": "DNS", "ports": ["53"], "desc": "DNS (53)"},
    "4": {
        "name": "DHCP",
        "ports": ["67", "68"],
        "desc": "DHCP сервер и клиент (67, 68)",
    },
    "5": {
        "name": "Почта",
        "ports": ["25", "587", "465", "143", "993", "110", "995"],
        "desc": "SMTP, Submission, SMTPS, IMAP, IMAPS, POP3, POP3S (25, 587, 465, 143, 993, 110, 995)",
    },
    "6": {
        "name": "FTP",
        "ports": ["20", "21"],
        "desc": "FTP данные и команды (20, 21)",
    },
    "7": {
        "name": "REMNAWAVE NODE",
        "ports": ["2222"],
        "desc": "REMNAWAVE NODE (2222)",
    },
    "8": {"name": "MySQL", "ports": ["3306"], "desc": "MySQL (3306)"},
    "9": {"name": "PostgreSQL", "ports": ["5432"], "desc": "PostgreSQL (5432)"},
    "10": {
        "name": "Все группы",
        "ports": [],
        "desc": "Все группы, кроме SSH",
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
            label="1 - 📦 Установить UFW",
            action=service.install,
            status_renderer=lambda status=install_status: status,
        ),
        MenuItem(
            key="2",
            label="2 - ▶️ Активировать UFW (установит при необходимости)",
            action=service.activate,
            status_renderer=lambda status=active_status: status,
        ),
        MenuItem(
            key="3",
            label="3 - ➕ Открыть порты из списка",
            action=lambda: _open_specific_ports(service),
        ),
        MenuItem(
            key="4",
            label="4 - ➖ Закрыть порты из списка",
            action=lambda: _close_specific_ports(service),
        ),
        MenuItem(
            key="5",
            label="5 - ➕ Открыть произвольный порт",
            action=lambda: _manage_custom_port(service, action="open"),
        ),
        MenuItem(
            key="6",
            label="6 - ➖ Закрыть произвольный порт",
            action=lambda: _manage_custom_port(service, action="close"),
        ),
        MenuItem(
            key="7",
            label="7 - 📊 Показать статус UFW",
            action=lambda: print(service.get_status()),
        ),
        MenuItem(
            key="8",
            label="8 - ⏹️  Отключить UFW",
            action=lambda: service.deactivate(confirm=True),
        ),
        MenuItem(
            key="9",
            label="9 - 🔄 Сбросить UFW (к настройкам по умолчанию)",
            action=lambda: service.reset(confirm=True),
        ),
        MenuItem(
            key="10",
            label="10 - 🗑️  Удалить UFW",
            action=lambda: service.uninstall(confirm=True),
        ),
    ]


def display_ufw_submenu(service: UfwService) -> str:
    """Отображает подменю UFW и возвращает выбор пользователя."""
    return prompt_service_submenu(
        header="Выберите действие:",
        items=_build_menu_items(service),
        info_label="00 - ℹ️ Информация о UFW",
    )


def _collect_ports_from_group_selection(*, include_ssh: bool) -> list[str]:
    for key, value in PORT_GROUPS.items():
        if not include_ssh and key == "1":
            continue
        print(f"{key} - {value['name']}: {value['desc']}")
    print("0 - Отмена")

    choice = input("Введите номер группы (или несколько через пробел): ").strip().split()
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
        print("❌ Не выбраны порты")
        return

    verb = "Открытие" if action == "open" else "Закрытие"
    service_action = service.open_port if action == "open" else service.close_port
    success_message = "открыт" if action == "open" else "закрыт"
    failure_message = "открыть" if action == "open" else "закрыть"

    print(f"\n🌐 {verb} портов: {', '.join(ports)}")
    success_count = 0
    for port in ports:
        if service_action(port):
            print(f"✅ Порт {port} {success_message}")
            success_count += 1
        else:
            print(f"❌ Не удалось {failure_message} порт {port}")

    if success_count > 0:
        print(f"✅ Успешно обработано {success_count} портов")
    else:
        print("❌ Не удалось обработать ни один порт")


def _open_specific_ports(service):
    """Интерактивное открытие конкретных портов."""
    print("Выберите порты для открытия:")
    _apply_ports(service, _collect_ports_from_group_selection(include_ssh=True), action="open")


def _close_specific_ports(service):
    """Интерактивное закрытие конкретных портов из готового списка."""
    print("Выберите порты для закрытия:")
    print("SSH (22) скрыт из этого списка для безопасного доступа к серверу.")
    _apply_ports(service, _collect_ports_from_group_selection(include_ssh=False), action="close")


def _manage_custom_port(service: UfwService, *, action: str) -> None:
    prompt = "Введите порт или правило (например 8080, 8080/tcp): "
    port = input(prompt).strip()
    if not port:
        print("❌ Порт не указан")
        return

    if action == "close" and port.lower() in UfwService.SSH_PORT_ALIASES:
        print("❌ Правило SSH нельзя удалить из соображений безопасности")
        return

    service_action = service.open_port if action == "open" else service.close_port
    success = service_action(port)
    if success:
        done = "открыт" if action == "open" else "закрыт"
        print(f"✅ Порт {port} {done}")
    else:
        failed = "открыть" if action == "open" else "закрыть"
        print(f"❌ Не удалось {failed} порт {port}")


def display_ufw_info():
    """Отображает информацию о UFW сервисе"""
    show_info_screen("🔥 UFW", UfwService().get_info_lines())


def interactive_run():
    """Entry point for UFW interactive mode."""
    service = UfwService()

    run_menu_loop(
        title="🔥 Управление UFW",
        header="Выберите действие:",
        items_factory=lambda: _build_menu_items(service),
        info_handler=display_ufw_info,
        exit_handler=return_to_main_menu,
        info_label="00 - ℹ️ Информация о UFW",
        exit_label="0 - 🏠 Вернуться в главное меню",
        intro_lines=["💡 По умолчанию: порт SSH (22) всегда разрешён для безопасности"],
        invalid_message="❌ Неверная опция, пожалуйста, попробуйте снова",
    )
