from app.interfaces.interactive.menu_utils import (
    build_standard_service_menu_items,
    prompt_service_submenu,
    return_to_main_menu,
    run_menu_loop,
    show_info_screen,
)
from app.services.docker import DockerService


def _build_menu_items(service: DockerService):
    return build_standard_service_menu_items(
        service=service,
        primary_key="1",
        primary_label="1 - 📦 Установить Docker",
        primary_action=service.install,
        primary_is_ok=service.is_installed,
        primary_ok_text="установлен",
        primary_fail_text="не установлен",
        uninstall_key="2",
        uninstall_label="2 - 🗑️ Удалить Docker",
        uninstall_action=lambda: service.uninstall(confirm=True),
        status_key="3",
        status_label="3 - 📊 Показать статус Docker",
    )


def display_docker_submenu(service: DockerService):
    """Отображает подменю для Docker с выбором действий"""
    return prompt_service_submenu(
        header="Доступные действия для Docker:",
        items=_build_menu_items(service),
        info_label="00 - ℹ️ Информация о Docker",
    )


def display_docker_info():
    """Отображает информацию о Docker сервисе"""
    show_info_screen("🐳 Docker Container Platform", DockerService().get_info_lines())


def interactive_run():
    service = DockerService()

    run_menu_loop(
        title="🐳 Docker Container Platform",
        header="Доступные действия для Docker:",
        items_factory=lambda: _build_menu_items(service),
        info_handler=display_docker_info,
        exit_handler=return_to_main_menu,
        info_label="00 - ℹ️ Информация о Docker",
        exit_label="0 - 🏠 Вернуться в главное меню",
    )
