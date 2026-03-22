from app.services.bbr import BBRService


def display_bbr_submenu():
    """Отображает подменю для BBR с выбором действий"""
    print("\nДоступные действия для BBR:")
    user_input = str(
        input(
            "1 - 🔌 Включить BBR\n2 - 🔓 Отключить BBR\n0 - 🏠 Вернуться в главное меню\nВведите номер: "
        )
    )
    return user_input


def interactive_run():
    bbr = BBRService()

    print("\n🌐 TCP BBR Congestion Control")
    print("BBR (Bottleneck Bandwidth and RTT) — это алгоритм управления перегрузками в TCP")
    print("Разработан Google для улучшения производительности сетевых соединений")
    print("Основные преимущества:")
    print("• Увеличение пропускной способности канала")
    print("• Снижение задержек (latency)")
    print("• Лучшая стабильность при высокой нагрузке")
    print("• Оптимизация для VPS и выделенных серверов")
    print("🔗 GitHub репозиторий: https://github.com/google/bbr")

    user_input = display_bbr_submenu()

    match user_input:
        case "0":
            from app.interfaces.interactive.run import run_interactive_script

            run_interactive_script()
        case "1":
            print("\nВключение BBR...")
            bbr.enable_bbr()
            print("\nBBR успешно включен!")
            interactive_run()
        case "2":
            print("\nОтключение BBR...")
            bbr.disable_bbr()
            print("\nBBR успешно отключен!")
            interactive_run()
        case _:
            print("Неверный ввод, попробуйте снова")
            interactive_run()
