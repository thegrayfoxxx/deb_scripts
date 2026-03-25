from app.services.docker import DockerService


def display_docker_submenu():
    """Отображает подменю для Docker с выбором действий"""
    print("\nДоступные действия для Docker:")
    user_input = str(
        input(
            "1 - 📦 Установить Docker\n"
            "2 - 🗑️ Удалить Docker\n"
            "00 - ℹ️ Информация о Docker\n"
            "0 - 🏠 Вернуться в главное меню\n"
            "Введите номер: "
        )
    )
    return user_input


def display_docker_info():
    """Отображает информацию о Docker сервисе"""
    print("\n🐳 Docker Container Platform")
    print("Docker — платформа для контейнеризации приложений и сервисов")
    print("Основные преимущества:")
    print("• Изоляция приложений в легковесных контейнерах")
    print("• Упрощение процесса развертывания")
    print("• Совместимость между различными системами")
    print("• Быстрый запуск и остановка сервисов")
    print("• Эффективное использование ресурсов")
    print("🔗 Официальный сайт: https://docker.com")
    print("\nДля возврата в меню нажмите любую клавишу")
    input()


def interactive_run():
    docker = DockerService()

    print("\n🐳 Docker Container Platform")

    user_input = display_docker_submenu()

    match user_input:
        case "0":
            from app.interfaces.interactive.run import run_interactive_script

            run_interactive_script()
        case "00":
            display_docker_info()
            interactive_run()
        case "1":
            print("\nУстановка Docker...")
            docker.install_docker()
            print("\nDocker успешно установлен!")
            interactive_run()
        case "2":
            print("\nУдаление Docker...")
            docker.uninstall_docker()
            print("\nDocker успешно удален!")
            interactive_run()
        case _:
            print("Неверный ввод, попробуйте снова")
            interactive_run()
