from app.interfaces.interactive import bbr, docker, fail2ban, traffic_guard, uv


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
            "1 - 🌐 BBR (TCP Congestion Control) - ускорение сети\n"
            "2 - 🐳 Docker - установка контейнеризации\n"
            "3 - 🛡️ Fail2Ban - защита от атак\n"
            "4 - ⚔️ TrafficGuard - комплексная защита\n"
            "5 - 🐍 UV - менеджер пакетов Python\n"
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
            bbr.interactive_run()
        case "2":
            docker.interactive_run()
        case "3":
            fail2ban.interactive_run()
        case "4":
            traffic_guard.interactive_run()
        case "5":
            uv.interactive_run()
        case _:
            print("❌ Неверный ввод, попробуйте снова")
            run_interactive_script()
