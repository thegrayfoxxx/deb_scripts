from app.interfaces.cli.non_interactive import run_non_interactive_commands
from app.interfaces.interactive.run import run_interactive_script
from app.utils.args_utils import app_args
from app.utils.logger import get_logger
from app.utils.permission_utils import check_root
from app.utils.update_utils import update_os

logger = get_logger(__name__)


def main():
    check_root()
    update_os()

    if app_args.install or app_args.uninstall:
        return 0 if run_non_interactive_commands(app_args) else 1
    else:
        run_interactive_script()
        return 0


def run_cli() -> int:
    """Запускает приложение и преобразует верхнеуровневые ошибки в код завершения."""
    try:
        return main()
    except KeyboardInterrupt:
        logger.info("👋 Выход...")
        return 130
    except PermissionError:
        logger.error(
            "🔐 Недостаточно прав для выполнения операции. Запустите скрипт с правами суперпользователя. (sudo)"
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(run_cli())
