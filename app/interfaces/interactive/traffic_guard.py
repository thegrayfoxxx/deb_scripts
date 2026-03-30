from app.interfaces.interactive.menu_utils import (
    build_standard_service_menu_items,
    prompt_service_submenu,
    return_to_main_menu,
    run_menu_loop,
    show_info_screen,
)
from app.services.traffic_guard import TrafficGuardService

INFO_LINES = [
    "TrafficGuard — комплексная система защиты сервера от сканирования и атак",
    "Основные возможности:",
    "• Блокировка подозрительных IP-адресов по множеству критериев",
    "• Защита от сканирования портов и сервисов",
    "• Мониторинг сетевой активности в реальном времени",
    "• Интеграция с системами firewall (iptables, nftables)",
    "• Автоматическое обновление списков заблокированных адресов",
    "• Поддержка IPv4 и IPv6",
    "🔗 GitHub репозиторий: https://github.com/DonMatteoVPN/TrafficGuard-auto",
]


def _build_menu_items(service: TrafficGuardService):
    return build_standard_service_menu_items(
        service=service,
        primary_key="1",
        primary_label="1 - 🔒 Установить TrafficGuard",
        primary_action=service.install_trafficguard,
        primary_is_ok=service.is_installed,
        primary_ok_text="установлен",
        primary_fail_text="не установлен",
        uninstall_key="2",
        uninstall_label="2 - 🔓 Удалить TrafficGuard",
        uninstall_action=lambda: service.uninstall_trafficguard(confirm=True),
        status_key="3",
        status_label="3 - 📊 Показать статус TrafficGuard",
    )


def display_trafficguard_submenu(service: TrafficGuardService):
    """Отображает подменю для TrafficGuard с выбором действий"""
    return prompt_service_submenu(
        header="Доступные действия для TrafficGuard:",
        items=_build_menu_items(service),
        info_label="00 - ℹ️ Информация о TrafficGuard",
    )


def display_trafficguard_info():
    """Отображает информацию о TrafficGuard сервисе"""
    show_info_screen("⚔️ TrafficGuard Server Protection", INFO_LINES)


def interactive_run():
    service = TrafficGuardService()

    run_menu_loop(
        title="⚔️ TrafficGuard Server Protection",
        header="Доступные действия для TrafficGuard:",
        items=_build_menu_items(service),
        info_handler=display_trafficguard_info,
        exit_handler=return_to_main_menu,
        info_label="00 - ℹ️ Информация о TrafficGuard",
        exit_label="0 - 🏠 Вернуться в главное меню",
    )
