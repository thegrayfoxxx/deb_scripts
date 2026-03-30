from app.utils.logger import get_logger
from app.utils.service_registry import get_service_entry

logger = get_logger(__name__)


def run_non_interactive_commands(app_args):
    """Run non-interactive installation or uninstallation commands"""
    all_ok = True

    if app_args.install:
        for code in app_args.install:
            entry = get_service_entry(code)
            if entry is None:
                logger.error(f"❌ Неизвестный код сервиса для установки: {code}")
                all_ok = False
                continue

            result = entry.service_factory().install()
            if result is False:
                all_ok = False

    if app_args.uninstall:
        for code in app_args.uninstall:
            entry = get_service_entry(code)
            if entry is None:
                logger.error(f"❌ Неизвестный код сервиса для удаления: {code}")
                all_ok = False
                continue

            result = entry.service_factory().uninstall()
            if result is False:
                all_ok = False

    return all_ok
