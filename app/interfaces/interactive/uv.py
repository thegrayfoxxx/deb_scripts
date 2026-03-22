from app.services.uv import UVService


def display_uv_submenu():
    """Отображает подменю для UV с выбором действий"""
    print("\nДоступные действия для UV:")
    user_input = str(
        input(
            "1 - 📦 Установить UV\n2 - 🗑️ Удалить UV\n0 - 🏠 Вернуться в главное меню\nВведите номер: "
        )
    )
    return user_input


def interactive_run():
    app = UVService()

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

    user_input = display_uv_submenu()

    match user_input:
        case "0":
            from app.interfaces.interactive.run import run_interactive_script

            run_interactive_script()
        case "1":
            print("\nУстановка UV...")
            app.install_uv()
            print("\nUV успешно установлен!")
            interactive_run()
        case "2":
            print("\nУдаление UV...")
            app.uninstall_uv()
            print("\nUV успешно удален!")
            interactive_run()
        case _:
            print("Неверный ввод, попробуйте снова")
            interactive_run()
