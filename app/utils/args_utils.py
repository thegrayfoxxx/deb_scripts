import argparse
import sys


def parse_args(argv: list[str] | None = None):
    raw_argv = sys.argv[1:] if argv is None else argv

    parser = argparse.ArgumentParser(
        description="Утилита для автоматизации DevOps задач в Linux",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error"],
        default="info",
        help="Уровень логирования для консоли: debug, info, warning, error (по умолчанию: info)",
    )
    parser.add_argument(
        "--mode",
        choices=["dev", "prod"],
        default="prod",
        help=argparse.SUPPRESS,
    )

    # Non-interactive mode arguments
    parser.add_argument(
        "--install",
        nargs="+",
        type=str,
        help="Режим неинтерактивной установки: 1=UFW, 2=BBR, 3=Docker, 4=Fail2Ban, 5=TrafficGuard, 6=UV",
    )
    parser.add_argument(
        "--uninstall",
        nargs="+",
        type=str,
        help="Режим неинтерактивного удаления: 1=UFW, 2=BBR, 3=Docker, 4=Fail2Ban, 5=TrafficGuard, 6=UV",
    )

    parsed = parser.parse_args(raw_argv)

    # Backward compatibility for older invocations that still use --mode.
    if "--mode" in raw_argv and "--log-level" not in raw_argv:
        parsed.log_level = "debug" if parsed.mode == "dev" else "info"

    return parsed


# Don't automatically parse args when running in pytest
if "pytest" in sys.modules:
    # During tests, provide a default configuration
    class DefaultArgs:
        mode = "prod"
        log_level = "info"
        install = None
        uninstall = None

    app_args = DefaultArgs()
else:
    # In normal execution, parse command line arguments
    app_args = parse_args()


def get_app_args():
    """Get the application arguments (for use in tests)"""
    return app_args
