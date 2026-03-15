from app.interfaces.interactive.run import run_interactive_script
from app.utils.logger import get_logger
from app.utils.permission_utils import check_root

logger = get_logger(__name__)


def main():
    check_root()
    run_interactive_script()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Выход...")
    except PermissionError:
        logger.error(
            "Недостаточно прав для выполнения операции. Запустите скрипт с правами суперпользователя. (sudo)"
        )
