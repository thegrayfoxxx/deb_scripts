from app.interfaces.interactive.menu_utils import (
    MenuItem,
    prompt_service_submenu,
    return_to_main_menu,
    run_menu_loop,
    show_info_screen,
)
from app.services.fail2ban import Fail2BanService
from app.utils.status_text import (
    activation_status_badge,
    installation_status_badge,
)


def _build_menu_items(service: Fail2BanService):
    install_status = installation_status_badge(service.is_installed())
    activation_status = activation_status_badge(service.is_active())

    return [
        MenuItem(
            key="1",
            label="1 - 📦 Установить Fail2Ban",
            action=service.install,
            status_renderer=lambda status=install_status: status,
        ),
        MenuItem(
            key="2",
            label="2 - 🔐 Активировать Fail2Ban",
            action=service.activate,
            status_renderer=lambda status=activation_status: status,
        ),
        MenuItem(
            key="3",
            label="3 - ⏹️ Отключить Fail2Ban",
            action=lambda: service.deactivate(confirm=True),
        ),
        MenuItem(
            key="4",
            label="4 - 🔓 Удалить Fail2Ban",
            action=lambda: service.uninstall(confirm=True),
        ),
        MenuItem(
            key="5",
            label="5 - 📊 Показать статус Fail2Ban",
            action=lambda: print(service.get_status()),
        ),
    ]


def display_fail2ban_submenu(service: Fail2BanService):
    """Отображает подменю для Fail2Ban с выбором действий"""
    return prompt_service_submenu(
        header="Доступные действия для Fail2Ban:",
        items=_build_menu_items(service),
        info_label="00 - ℹ️ Информация о Fail2Ban",
    )


def display_fail2ban_info():
    """Отображает информацию о Fail2Ban сервисе"""
    show_info_screen(
        "🛡️ Fail2Ban Intrusion Prevention Software", Fail2BanService().get_info_lines()
    )


def interactive_run():
    service = Fail2BanService()

    run_menu_loop(
        title="🛡️ Fail2Ban Intrusion Prevention Software",
        header="Доступные действия для Fail2Ban:",
        items_factory=lambda: _build_menu_items(service),
        info_handler=display_fail2ban_info,
        exit_handler=return_to_main_menu,
        info_label="00 - ℹ️ Информация о Fail2Ban",
        exit_label="0 - 🏠 Вернуться в главное меню",
    )
