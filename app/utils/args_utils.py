import argparse

from app.utils.service_registry import format_service_codes_help


def parse_args(argv: list[str] | None = None):
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
        "--install",
        nargs="+",
        type=str,
        help=f"Режим неинтерактивной установки: {format_service_codes_help()}",
    )
    parser.add_argument(
        "--uninstall",
        nargs="+",
        type=str,
        help=f"Режим неинтерактивного удаления: {format_service_codes_help()}",
    )
    return parser.parse_args(argv)
