from app.interfaces.interactive import bbr, docker, fail2ban, traffic_guard, ufw, uv
from app.interfaces.interactive.menu_utils import (
    MenuItem,
    prompt_menu,
    run_menu_loop,
    show_info_screen,
)
from app.interfaces.interactive.status_utils import status_badge
from app.services.bbr import BBRService
from app.services.docker import DockerService
from app.services.fail2ban import Fail2BanService
from app.services.traffic_guard import TrafficGuardService
from app.services.ufw import UfwService
from app.services.uv import UVService

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


def _ufw_status(service: UfwService) -> str:
    if not service.is_installed():
        return "🔴 не установлен"
    return status_badge(service.is_active(), "включен", "выключен")


def _bbr_status(service: BBRService) -> str:
    return status_badge(service.is_active(), "включен", "выключен")


def _docker_status(service: DockerService) -> str:
    return status_badge(service.is_installed(), "установлен", "не установлен")


def _fail2ban_status(service: Fail2BanService) -> str:
    if not service.is_installed():
        return "🔴 не установлен"
    return status_badge(service.is_active(), "активен", "не активен")


def _traffic_guard_status(service: TrafficGuardService) -> str:
    if not service.is_installed():
        return "🔴 не установлен"
    return status_badge(service.is_active(), "активен", "не активен")


def _uv_status(service: UVService) -> str:
    return status_badge(service.is_installed(), "установлен", "не установлен")


def _build_main_menu_items() -> list[MenuItem]:
    ufw_service = UfwService()
    bbr_service = BBRService()
    docker_service = DockerService()
    fail2ban_service = Fail2BanService()
    traffic_guard_service = TrafficGuardService()
    uv_service = UVService()

    return [
        MenuItem(
            key="1",
            label="1 - 🔥 UFW - uncomplicated firewall (межсетевой экран)",
            action=ufw.interactive_run,
            status_renderer=lambda: _ufw_status(ufw_service),
        ),
        MenuItem(
            key="2",
            label="2 - 🌐 BBR (TCP Congestion Control) - ускорение сети",
            action=bbr.interactive_run,
            status_renderer=lambda: _bbr_status(bbr_service),
        ),
        MenuItem(
            key="3",
            label="3 - 🐳 Docker - установка контейнеризации",
            action=docker.interactive_run,
            status_renderer=lambda: _docker_status(docker_service),
        ),
        MenuItem(
            key="4",
            label="4 - 🛡️ Fail2Ban - защита от атак",
            action=fail2ban.interactive_run,
            status_renderer=lambda: _fail2ban_status(fail2ban_service),
        ),
        MenuItem(
            key="5",
            label="5 - ⚔️ TrafficGuard - комплексная защита",
            action=traffic_guard.interactive_run,
            status_renderer=lambda: _traffic_guard_status(traffic_guard_service),
        ),
        MenuItem(
            key="6",
            label="6 - 🐍 UV - менеджер пакетов Python",
            action=uv.interactive_run,
            status_renderer=lambda: _uv_status(uv_service),
        ),
    ]


def display_main_menu() -> str:
    """Отображает главное интерактивное меню и возвращает выбор пользователя."""
    return prompt_menu(
        header="Выберите утилиту для работы:",
        items=_build_main_menu_items(),
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
        items=_build_main_menu_items(),
        info_handler=display_program_info,
        exit_handler=_exit_program,
        info_label="00 - ℹ️ Информация о программе",
        exit_label="0 - ❌ Выход",
        invalid_message="❌ Неверный ввод, попробуйте снова",
    )
