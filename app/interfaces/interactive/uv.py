from app.services.uv import UVService


def display_uv_submenu():
    """Отображает подменю для UV с выбором действий"""
    print("\nДоступные действия для UV:")
    user_input = str(
        input(
            "1 - 📦 Установить UV\n2 - 🗑️ Удалить UV\n00 - ℹ️ Информация о UV\n0 - 🏠 Вернуться в главное меню\nВведите номер: "
        )
    )
    return user_input


def display_uv_info():
    """Отображает информацию о UV сервисе"""
    print("\n🐍 UV Python Package Manager")
    print("UV — современный и быстрый менеджер пакетов Python")
    print("Основные преимущества:")
    print("• Высокая скорость установки пакетов (в 10-100 раз быстрее, чем pip)")
    print("• Современная система разрешения зависимостей")
    print("• Альтернатива для pip, pipenv, poetry и других")
    print("• Надежная изоляция окружений")
    print("• Улучшенная безопасность при установке пакетов")
    print("• Полная совместимость с PyPI и системой пакетов Python")
    print("🔗 GitHub репозиторий: https://github.com/astral-sh/uv")
    print("🔗 Официальный сайт: https://astral.sh")
    print("\nДля возврата в меню нажмите любую клавишу")
    input()


def interactive_run():
    app = UVService()

    print("\n🐍 UV Python Package Manager")

    user_input = display_uv_submenu()

    match user_input:
        case "0":
            from app.interfaces.interactive.run import run_interactive_script

            run_interactive_script()
        case "00":
            display_uv_info()
            interactive_run()
        case "1":
            app.install_uv()
            interactive_run()
        case "2":
            app.uninstall_uv(confirm=True)
            interactive_run()
        case _:
            interactive_run()
