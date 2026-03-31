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
            label="1 - 🔧 Установить UFW",
            action=service.install,
            status_renderer=lambda status=install_status: status,
        ),
        MenuItem(
            key="2",
            label="2 - 🔐 Включить UFW (установит если нет)",
            action=service.activate,
            status_renderer=lambda status=active_status: status,
        ),
        MenuItem(
            key="3",
            label="3 - 🌐 Открыть порты (интерактивный выбор)",
            action=lambda: _open_specific_ports(service),
        ),
        MenuItem(
            key="4",
            label="4 - 📊 Показать статус UFW",
            action=lambda: print(service.get_status()),
        ),
        MenuItem(
            key="5",
            label="5 - ⏹️  Отключить UFW",
            action=lambda: service.deactivate(confirm=True),
        ),
        MenuItem(
            key="6",
            label="6 - 🔄 Сбросить UFW (к настройкам по умолчанию)",
            action=lambda: service.reset(confirm=True),
        ),
        MenuItem(
            key="7",
            label="7 - 🗑️  Удалить UFW",
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


def _open_specific_ports(service):
    """Интерактивное открытие конкретных портов."""
    print("Выберите порты для открытия:")

    port_groups = {
        "1": {"name": "SSH", "ports": ["22"], "desc": "SSH (22, уже открыт)"},
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
            "name": "Все вышеуказанные",
            "ports": [],
            "desc": "Выбрать все группы (кроме SSH)",
        },
    }

    for key, value in port_groups.items():
        print(f"{key} - {value['name']}: {value['desc']}")

    print("0 - Отмена")

    choice = input("Введите номер группы (или несколько через пробел): ").strip().split()

    if "0" in choice:
        print("❌ Открытие портов отменено")
        return

    all_ports_to_open = set()

    for option in choice:
        if option in port_groups:
            if option == "10":
                for key, value in port_groups.items():
                    if key not in {"1", "10"}:
                        all_ports_to_open.update(value["ports"])
            elif option != "1":
                all_ports_to_open.update(port_groups[option]["ports"])

    if all_ports_to_open:
        print(f"\n🌐 Открытие портов: {', '.join(sorted(all_ports_to_open))}")
        success_count = 0
        for port in sorted(all_ports_to_open):
            result = service.open_port(port)
            if result:
                print(f"✅ Порт {port} открыт")
                success_count += 1
            else:
                print(f"❌ Не удалось открыть порт {port}")

        if success_count > 0:
            print(f"✅ Успешно открыто {success_count} портов")
        else:
            print("❌ Не удалось открыть ни один порт")
    else:
        print("❌ Не выбраны порты для открытия")


def display_ufw_info():
    """Отображает информацию о UFW сервисе"""
    show_info_screen("🔥 UFW (Uncomplicated Firewall)", UfwService().get_info_lines())


def interactive_run():
    """Entry point for UFW interactive mode."""
    service = UfwService()

    run_menu_loop(
        title="🔥 Управление UFW (Межсетевой экран)",
        header="Выберите действие:",
        items_factory=lambda: _build_menu_items(service),
        info_handler=display_ufw_info,
        exit_handler=return_to_main_menu,
        info_label="00 - ℹ️ Информация о UFW",
        exit_label="0 - 🏠 Вернуться в главное меню",
        intro_lines=["💡 По умолчанию: порт SSH (22) всегда разрешён для безопасности"],
        invalid_message="❌ Неверная опция, пожалуйста, попробуйте снова",
    )
