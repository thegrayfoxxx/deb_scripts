from app.services.bbr import BBRService


def display_bbr_submenu():
    """Отображает подменю для BBR с выбором действий"""
    print("\nДоступные действия для BBR:")
    user_input = str(
        input(
            "1 - 🔌 Включить BBR\n2 - 🔓 Отключить BBR\n00 - ℹ️ Информация о BBR\n0 - 🏠 Вернуться в главное меню\nВведите номер: "
        )
    )
    return user_input


def display_bbr_info():
    """Отображает информацию о BBR сервисе"""
    print("\n🌐 TCP BBR Congestion Control")
    print("BBR (Bottleneck Bandwidth and RTT) — это алгоритм управления перегрузками в TCP")
    print("Разработан Google для улучшения производительности сетевых соединений")
    print("Основные преимущества:")
    print("• Увеличение пропускной способности канала")
    print("• Снижение задержек (latency)")
    print("• Лучшая стабильность при высокой нагрузке")
    print("• Оптимизация для VPS и выделенных серверов")
    print("🔗 GitHub репозиторий: https://github.com/google/bbr")
    print("\nДля возврата в меню нажмите любую клавишу")
    input()


def interactive_run():
    bbr = BBRService()

    print("\n🌐 TCP BBR Congestion Control")

    user_input = display_bbr_submenu()

    match user_input:
        case "0":
            from app.interfaces.interactive.run import run_interactive_script

            run_interactive_script()
        case "00":
            display_bbr_info()
            interactive_run()
        case "1":
            bbr.enable_bbr()
            interactive_run()
        case "2":
            bbr.disable_bbr(confirm=True)
            interactive_run()
        case _:
            interactive_run()
