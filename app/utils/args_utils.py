import argparse
import sys


def parse_args():
    parser = argparse.ArgumentParser(
        description="Утилита для автоматизации DevOps задач в Linux",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "--mode",
        choices=["dev", "prod"],
        default="prod",
        help="Режим работы приложения: dev (для разработки) или prod (продакшен по умолчанию)",
    )

    # Non-interactive mode arguments
    parser.add_argument(
        "--install",
        nargs="+",
        type=str,
        help="Режим неинтерактивной установки: 1=BBR, 2=Docker, 3=Fail2Ban, 4=TrafficGuard, 5=UV",
    )
    parser.add_argument(
        "--uninstall",
        nargs="+",
        type=str,
        help="Режим неинтерактивного удаления: 1=BBR, 2=Docker, 3=Fail2Ban, 4=TrafficGuard, 5=UV",
    )

    return parser.parse_args()


# Don't automatically parse args when running in pytest
if "pytest" in sys.modules:
    # During tests, provide a default configuration
    class DefaultArgs:
        mode = "prod"

    app_args = DefaultArgs()
else:
    # In normal execution, parse command line arguments
    app_args = parse_args()


def get_app_args():
    """Get the application arguments (for use in tests)"""
    return app_args
