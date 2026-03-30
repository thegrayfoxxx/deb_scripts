from app.interfaces.interactive.menu_utils import (
    build_standard_service_menu_items,
    prompt_service_submenu,
    return_to_main_menu,
    run_menu_loop,
    show_info_screen,
)
from app.services.bbr import BBRService

INFO_LINES = [
    "BBR (Bottleneck Bandwidth and RTT) — это алгоритм управления перегрузками в TCP",
    "Разработан Google для улучшения производительности сетевых соединений",
    "Основные преимущества:",
    "• Увеличение пропускной способности канала",
    "• Снижение задержек (latency)",
    "• Лучшая стабильность при высокой нагрузке",
    "• Оптимизация для VPS и выделенных серверов",
    "🔗 GitHub репозиторий: https://github.com/google/bbr",
]


def _build_menu_items(service: BBRService):
    return build_standard_service_menu_items(
        service=service,
        primary_key="1",
        primary_label="1 - 🔌 Включить BBR",
        primary_action=service.enable_bbr,
        primary_is_ok=service.is_active,
        primary_ok_text="включен",
        primary_fail_text="выключен",
        uninstall_key="2",
        uninstall_label="2 - 🔓 Отключить BBR",
        uninstall_action=lambda: service.disable_bbr(confirm=True),
        status_key="3",
        status_label="3 - 📊 Показать статус BBR",
    )


def display_bbr_submenu(service: BBRService):
    """Отображает подменю для BBR с выбором действий"""
    return prompt_service_submenu(
        header="Доступные действия для BBR:",
        items=_build_menu_items(service),
        info_label="00 - ℹ️ Информация о BBR",
    )


def display_bbr_info():
    """Отображает информацию о BBR сервисе"""
    show_info_screen("🌐 TCP BBR Congestion Control", INFO_LINES)


def interactive_run():
    service = BBRService()

    run_menu_loop(
        title="🌐 TCP BBR Congestion Control",
        header="Доступные действия для BBR:",
        items=_build_menu_items(service),
        info_handler=display_bbr_info,
        exit_handler=return_to_main_menu,
        info_label="00 - ℹ️ Информация о BBR",
        exit_label="0 - 🏠 Вернуться в главное меню",
    )
