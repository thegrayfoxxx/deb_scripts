from app.bootstrap.args import parse_args
from app.bootstrap.logger import get_logger, set_default_console_level
from app.bootstrap.permissions import check_root
from app.bootstrap.update_os import update_os
from app.interfaces.cli.non_interactive import run_non_interactive_commands
from app.interfaces.menu.run import run_interactive_script

logger = get_logger(__name__)

NON_INTERACTIVE_OPTIONS = (
    "install",
    "uninstall",
    "activate",
    "deactivate",
    "status",
    "info",
)


def _has_non_interactive_request(args) -> bool:
    return any(getattr(args, option_name) is not None for option_name in NON_INTERACTIVE_OPTIONS)


def main(argv: list[str] | None = None):
    args = parse_args(argv)
    set_default_console_level(args.log_level)

    check_root()
    update_os()

    if _has_non_interactive_request(args):
        return 0 if run_non_interactive_commands(args) else 1

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
