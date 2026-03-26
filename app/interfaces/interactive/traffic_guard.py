from app.services.traffic_guard import TrafficGuardService


def display_trafficguard_submenu():
    """Отображает подменю для TrafficGuard с выбором действий"""
    print("\nДоступные действия для TrafficGuard:")
    user_input = str(
        input(
            "1 - 🔒 Установить TrafficGuard\n"
            "2 - 🔓 Удалить TrafficGuard\n"
            "00 - ℹ️ Информация о TrafficGuard\n"
            "0 - 🏠 Вернуться в главное меню\n"
            "Введите номер: "
        )
    )
    return user_input


def display_trafficguard_info():
    """Отображает информацию о TrafficGuard сервисе"""
    print("\n⚔️ TrafficGuard Server Protection")
    print("TrafficGuard — комплексная система защиты сервера от сканирования и атак")
    print("Основные возможности:")
    print("• Блокировка подозрительных IP-адресов по множеству критериев")
    print("• Защита от сканирования портов и сервисов")
    print("• Мониторинг сетевой активности в реальном времени")
    print("• Интеграция с системами firewall (iptables, nftables)")
    print("• Автоматическое обновление списков заблокированных адресов")
    print("• Поддержка IPv4 и IPv6")
    print("🔗 GitHub репозиторий: https://github.com/DonMatteoVPN/TrafficGuard-auto")
    print("\nДля возврата в меню нажмите любую клавишу")
    input()


def interactive_run():
    traffic_guard = TrafficGuardService()

    print("\n⚔️ TrafficGuard Server Protection")

    user_input = display_trafficguard_submenu()

    match user_input:
        case "0":
            from app.interfaces.interactive.run import run_interactive_script

            run_interactive_script()
        case "00":
            display_trafficguard_info()
            interactive_run()
        case "1":
            traffic_guard.install_trafficguard()
            interactive_run()
        case "2":
            traffic_guard.uninstall_trafficguard(confirm=True)
            interactive_run()
        case _:
            interactive_run()
