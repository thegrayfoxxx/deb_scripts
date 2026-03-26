from app.services.ufw import UfwService
from app.utils.logger import get_logger

logger = get_logger(__name__)


def show_ufw_menu():
    """Интерактивное меню для управления UFW."""
    service = UfwService()

    print("\n🔥 Управление UFW (Межсетевой экран)")
    print("💡 По умолчанию: порт SSH (22) всегда разрешён для безопасности")

    while True:
        print("\nВыберите действие:")
        user_input = str(
            input(
                "1 - 🔧 Установить UFW\n"
                "2 - 🔐 Включить UFW (установит если нет)\n"
                "3 - 🌐 Открыть порты (интерактивный выбор)\n"
                "4 - 📊 Показать статус UFW\n"
                "5 - ⏹️  Отключить UFW\n"
                "6 - 🔄 Сбросить UFW (к настройкам по умолчанию)\n"
                "7 - 🗑️  Удалить UFW\n"
                "00 - ℹ️ Информация о UFW\n"
                "0 - 🏠 Вернуться в главное меню\n"
                "Введите номер: "
            )
        )

        match user_input:
            case "0":
                print("🏠 Возврат в главное меню...")
                from app.interfaces.interactive.run import run_interactive_script

                run_interactive_script()
            case "00":
                display_ufw_info()
                show_ufw_menu()
            case "1":
                service.install()
            case "2":
                service.enable_with_ssh_only()
            case "3":
                _open_specific_ports(service)
            case "4":
                status = service.get_status()
                print(status)
            case "5":
                service.disable(confirm=True)
            case "6":
                service.reset(confirm=True)
            case "7":
                service.uninstall(confirm=True)
            case _:
                print("❌ Неверная опция, пожалуйста, попробуйте снова")


def _open_specific_ports(service):
    """Интерактивное открытие конкретных портов."""
    print("Выберите порты для открытия:")

    # Группы портов
    port_groups = {
        "1": {"name": "SSH", "ports": ["22"], "desc": "SSH (22, уже открыт)"},
        "2": {"name": "Web-сервер", "ports": ["80", "443"], "desc": "HTTP и HTTPS (80, 443)"},
        "3": {"name": "DNS", "ports": ["53"], "desc": "DNS (53)"},
        "4": {"name": "DHCP", "ports": ["67", "68"], "desc": "DHCP сервер и клиент (67, 68)"},
        "5": {
            "name": "Почта",
            "ports": ["25", "587", "465", "143", "993", "110", "995"],
            "desc": "SMTP, Submission, SMTPS, IMAP, IMAPS, POP3, POP3S (25, 587, 465, 143, 993, 110, 995)",
        },
        "6": {"name": "FTP", "ports": ["20", "21"], "desc": "FTP данные и команды (20, 21)"},
        "7": {"name": "REMNAWAVE NODE", "ports": ["2222"], "desc": "REMNAWAVE NODE (2222)"},
        "8": {"name": "MySQL", "ports": ["3306"], "desc": "MySQL (3306)"},
        "9": {"name": "PostgreSQL", "ports": ["5432"], "desc": "PostgreSQL (5432)"},
        "10": {"name": "Все вышеуказанные", "ports": [], "desc": "Выбрать все группы (кроме SSH)"},
    }

    # Отображение опций
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
            if option == "9":  # Все группы
                for key, value in port_groups.items():
                    if key != "9" and key != "3":  # Исключаем "Все вышеуказанные" и SSH
                        all_ports_to_open.update(value["ports"])
            elif option != "3":  # Исключаем SSH, так как он уже открыт
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
    print("\n🔥 UFW (Uncomplicated Firewall)")
    print("UFW - это интерфейс для управления межсетевым экраном iptables")
    print("Предназначен для упрощения настройки правил межсетевого экрана")
    print("Основные возможности:")
    print("• Блокировка/разрешение сетевых соединений")
    print("• Настройка правил для конкретных портов и служб")
    print("• Защита от нежелательных входящих соединений")
    print("• Управление через простые команды")
    print("🔗 Официальная документация: https://help.ubuntu.com/community/UFW")
    print("\nДля возврата в меню нажмите любую клавишу")
    input()


def interactive_run():
    """Entry point for UFW interactive mode."""
    show_ufw_menu()
