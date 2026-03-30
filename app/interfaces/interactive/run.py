from app.interfaces.interactive.menu_utils import (
    prompt_menu,
    run_menu_loop,
    show_info_screen,
)
from app.utils.service_registry import build_main_menu_items

PROGRAM_INFO_LINES = [
    "📋 Этот инструмент помогает автоматизировать задачи DevOps в Linux:",
    "• Установка и настройка сервисов",
    "• Оптимизация производительности",
    "• Защита сервера",
    "🔗 GitHub репозиторий: https://github.com/thegrayfoxxx/deb_scripts",
]


def display_program_info():
    """Отображает информацию о программе и её возможностях"""
    show_info_screen("🤖 О программе deb_scripts", PROGRAM_INFO_LINES)


def display_main_menu() -> str:
    """Отображает главное интерактивное меню и возвращает выбор пользователя."""
    return prompt_menu(
        header="Выберите утилиту для работы:",
        items=build_main_menu_items(),
        info_label="00 - ℹ️ Информация о программе",
        exit_label="0 - ❌ Выход",
    )


def _exit_program() -> None:
    print("👋 До свидания!")
    exit()


def run_interactive_script():
    run_menu_loop(
        title="🤖 Добро пожаловать в deb_scripts! 🤖",
        header="Выберите утилиту для работы:",
        items=build_main_menu_items(),
        info_handler=display_program_info,
        exit_handler=_exit_program,
        info_label="00 - ℹ️ Информация о программе",
        exit_label="0 - ❌ Выход",
        invalid_message="❌ Неверный ввод, попробуйте снова",
    )
