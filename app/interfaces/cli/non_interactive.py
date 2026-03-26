from app.services.bbr import BBRService
from app.services.docker import DockerService
from app.services.fail2ban import Fail2BanService
from app.services.traffic_guard import TrafficGuardService
from app.services.ufw import UfwService
from app.services.uv import UVService
from app.utils.logger import get_logger

logger = get_logger(__name__)


def run_non_interactive_commands(app_args):
    """Run non-interactive installation or uninstallation commands"""
    logger.info("⚙️ Запуск в неинтерактивном режиме...")

    # Dictionary mapping service codes to service classes and their methods
    services_map = {
        "1": ("UFW", UfwService(), "install", "uninstall"),
        "2": ("BBR", BBRService(), "enable_bbr", "disable_bbr"),
        "3": ("Docker", DockerService(), "install_docker", "uninstall_docker"),
        "4": ("Fail2Ban", Fail2BanService(), "install_fail2ban", "uninstall_fail2ban"),
        "5": (
            "TrafficGuard",
            TrafficGuardService(),
            "install_trafficguard",
            "uninstall_trafficguard",
        ),
        "6": ("UV", UVService(), "install_uv", "uninstall_uv"),
    }

    # Process installation requests
    if app_args.install:
        for code in app_args.install:
            if code in services_map:
                service_name, service_instance, install_method_name, _ = services_map[code]
                logger.info(f"📦 Установка {service_name}...")

                # Get the install method dynamically
                install_method = getattr(service_instance, install_method_name)
                install_method()

                logger.info(f"✅ {service_name} установка завершена")
            else:
                logger.error(f"❌ Неизвестный код сервиса для установки: {code}")

    # Process uninstallation requests
    if app_args.uninstall:
        for code in app_args.uninstall:
            if code in services_map:
                service_name, service_instance, _, uninstall_method_name = services_map[code]
                logger.info(f"🗑️ Удаление {service_name}...")

                # Get the uninstall method dynamically
                uninstall_method = getattr(service_instance, uninstall_method_name)
                uninstall_method()

                logger.info(f"✅ {service_name} удаление завершено")
            else:
                logger.error(f"❌ Неизвестный код сервиса для удаления: {code}")

    logger.info("✅ Неинтерактивные команды выполнены.")
