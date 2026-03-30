from app.interfaces.interactive.menu_utils import (
    build_standard_service_menu_items,
    prompt_service_submenu,
    return_to_main_menu,
    run_menu_loop,
    show_info_screen,
)
from app.services.fail2ban import Fail2BanService

INFO_LINES = [
    "Fail2Ban — система автоматической защиты от атак подбора паролей и брутфорса",
    "Основные возможности:",
    "• Мониторинг логов систем и приложений",
    "• Автоматическая блокировка подозрительных IP-адресов",
    "• Защита от DDoS-атак и сканирования портов",
    "• Настраиваемые правила фильтрации",
    "• Поддержка различных сервисов (SSH, FTP, HTTP и др.)",
    "• Логирование всех действий безопасности",
    "🔗 GitHub репозиторий: https://github.com/fail2ban/fail2ban",
]


def _build_menu_items(service: Fail2BanService):
    return build_standard_service_menu_items(
        service=service,
        primary_key="1",
        primary_label="1 - 🔒 Установить Fail2Ban",
        primary_action=service.install_fail2ban,
        primary_is_ok=service.is_installed,
        primary_ok_text="установлен",
        primary_fail_text="не установлен",
        uninstall_key="2",
        uninstall_label="2 - 🔓 Удалить Fail2Ban",
        uninstall_action=lambda: service.uninstall_fail2ban(confirm=True),
        status_key="3",
        status_label="3 - 📊 Показать статус Fail2Ban",
    )


def display_fail2ban_submenu(service: Fail2BanService):
    """Отображает подменю для Fail2Ban с выбором действий"""
    return prompt_service_submenu(
        header="Доступные действия для Fail2Ban:",
        items=_build_menu_items(service),
        info_label="00 - ℹ️ Информация о Fail2Ban",
    )


def display_fail2ban_info():
    """Отображает информацию о Fail2Ban сервисе"""
    show_info_screen("🛡️ Fail2Ban Intrusion Prevention Software", INFO_LINES)


def interactive_run():
    service = Fail2BanService()

    run_menu_loop(
        title="🛡️ Fail2Ban Intrusion Prevention Software",
        header="Доступные действия для Fail2Ban:",
        items=_build_menu_items(service),
        info_handler=display_fail2ban_info,
        exit_handler=return_to_main_menu,
        info_label="00 - ℹ️ Информация о Fail2Ban",
        exit_label="0 - 🏠 Вернуться в главное меню",
    )
