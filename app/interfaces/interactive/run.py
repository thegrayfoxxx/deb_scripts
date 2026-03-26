from app.interfaces.interactive import bbr, docker, fail2ban, traffic_guard, ufw, uv


def display_program_info():
    """Отображает информацию о программе и её возможностях"""
    print("\n📋 Этот инструмент помогает автоматизировать задачи DevOps в Linux:")
    print("• Установка и настройка сервисов")
    print("• Оптимизация производительности")
    print("• Защита сервера")
    print("🔗 GitHub репозиторий: https://github.com/thegrayfoxxx/deb_scripts")
    print("\nДля возврата в главное меню нажмите любую клавишу")
    input()


def run_interactive_script():
    print("🤖 Добро пожаловать в deb_scripts! 🤖")

    print("\nВыберите утилиту для работы:")
    user_input = str(
        input(
            "1 - 🔥 UFW - uncomplicated firewall (межсетевой экран)\n"
            "2 - 🌐 BBR (TCP Congestion Control) - ускорение сети\n"
            "3 - 🐳 Docker - установка контейнеризации\n"
            "4 - 🛡️ Fail2Ban - защита от атак\n"
            "5 - ⚔️ TrafficGuard - комплексная защита\n"
            "6 - 🐍 UV - менеджер пакетов Python\n"
            "00 - ℹ️ Информация о программе\n"
            "0 - ❌ Выход\n"
            "Введите номер: "
        )
    )
    match user_input:
        case "0":
            print("👋 До свидания!")
            exit()
        case "00":
            display_program_info()
            run_interactive_script()
        case "1":
            ufw.interactive_run()
        case "2":
            bbr.interactive_run()
        case "3":
            docker.interactive_run()
        case "4":
            fail2ban.interactive_run()
        case "5":
            traffic_guard.interactive_run()
        case "6":
            uv.interactive_run()
        case _:
            print("❌ Неверный ввод, попробуйте снова")
            run_interactive_script()
