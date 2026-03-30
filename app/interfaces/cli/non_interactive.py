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
    services_map = {
        "1": UfwService(),
        "2": BBRService(),
        "3": DockerService(),
        "4": Fail2BanService(),
        "5": TrafficGuardService(),
        "6": UVService(),
    }
    all_ok = True

    if app_args.install:
        for code in app_args.install:
            if code in services_map:
                result = services_map[code].install()
                if result is False:
                    all_ok = False
            else:
                logger.error(f"❌ Неизвестный код сервиса для установки: {code}")
                all_ok = False

    if app_args.uninstall:
        for code in app_args.uninstall:
            if code in services_map:
                result = services_map[code].uninstall()
                if result is False:
                    all_ok = False
            else:
                logger.error(f"❌ Неизвестный код сервиса для удаления: {code}")
                all_ok = False

    return all_ok
