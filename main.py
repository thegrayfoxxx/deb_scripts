from app.interfaces.cli.non_interactive import run_non_interactive_commands
from app.interfaces.interactive.run import run_interactive_script
from app.utils.args_utils import app_args
from app.utils.logger import get_logger
from app.utils.permission_utils import check_root

logger = get_logger(__name__)


def main():
    check_root()

    # Handle non-interactive commands
    if app_args.install or app_args.uninstall:
        run_non_interactive_commands(app_args)
    else:
        run_interactive_script()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("👋 Выход...")
    except PermissionError:
        logger.error(
            "🔐 Недостаточно прав для выполнения операции. Запустите скрипт с правами суперпользователя. (sudo)"
        )
