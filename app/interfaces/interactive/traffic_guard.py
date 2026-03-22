from app.services.traffic_guard import TrafficGuardService


def display_trafficguard_submenu():
    """Отображает подменю для TrafficGuard с выбором действий"""
    print("\nДоступные действия для TrafficGuard:")
    user_input = str(
        input(
            "1 - 🔒 Установить TrafficGuard\n"
            "2 - 🔓 Удалить TrafficGuard\n"
            "0 - 🏠 Вернуться в главное меню\n"
            "Введите номер: "
        )
    )
    return user_input


def interactive_run():
    traffic_guard = TrafficGuardService()

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

    user_input = display_trafficguard_submenu()

    match user_input:
        case "0":
            from app.interfaces.interactive.run import run_interactive_script

            run_interactive_script()
        case "1":
            print("\nУстановка TrafficGuard...")
            traffic_guard.install_trafficguard()
            print("\nTrafficGuard успешно установлен!")
            interactive_run()
        case "2":
            print("\nУдаление TrafficGuard...")
            traffic_guard.uninstall_trafficguard()
            print("\nTrafficGuard успешно удален!")
            interactive_run()
        case _:
            print("Неверный ввод, попробуйте снова")
            interactive_run()
