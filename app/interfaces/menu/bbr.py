from app.core.status import (
    activation_status_badge,
    installation_status_badge,
)
from app.interfaces.menu.menu_utils import (
    MenuItem,
    prompt_service_submenu,
    return_to_main_menu,
    run_menu_loop,
    show_info_screen,
)
from app.services.bbr import BBRService


def _build_menu_items(service: BBRService):
    install_status = installation_status_badge(service.is_installed())
    activation_status = activation_status_badge(service.is_active())

    return [
        MenuItem(
            key="1",
            label="1 - 📦 Подготовить BBR",
            action=service.install,
            status_renderer=lambda status=install_status: status,
        ),
        MenuItem(
            key="2",
            label="2 - ▶️ Активировать BBR (подготовит при необходимости)",
            action=service.activate,
            status_renderer=lambda status=activation_status: status,
        ),
        MenuItem(
            key="3",
            label="3 - ⏹️ Отключить BBR",
            action=lambda: service.deactivate(confirm=True),
        ),
        MenuItem(
            key="4",
            label="4 - 🗑️ Удалить конфигурацию BBR",
            action=lambda: service.uninstall(confirm=True),
        ),
        MenuItem(
            key="5",
            label="5 - 📊 Показать статус BBR",
            action=lambda: print(service.get_status()),
        ),
    ]


def display_bbr_submenu(service: BBRService):
    """Отображает подменю для BBR с выбором действий"""
    return prompt_service_submenu(
        header="Доступные действия для BBR:",
        items=_build_menu_items(service),
        info_label="00 - ℹ️ Информация о BBR",
    )


def display_bbr_info():
    """Отображает информацию о BBR сервисе"""
    show_info_screen("🌐 BBR", BBRService().get_info_lines())


def interactive_run():
    service = BBRService()

    run_menu_loop(
        title="🌐 Управление BBR",
        header="Доступные действия для BBR:",
        items_factory=lambda: _build_menu_items(service),
        info_handler=display_bbr_info,
        exit_handler=return_to_main_menu,
        info_label="00 - ℹ️ Информация о BBR",
        exit_label="0 - 🏠 Вернуться в главное меню",
    )
