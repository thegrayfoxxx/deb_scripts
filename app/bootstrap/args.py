import argparse

from app.core.service_registry import format_service_codes_help

NON_INTERACTIVE_OPTIONS = ("install", "uninstall", "activate", "deactivate", "status", "info")


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
        nargs="*",
        type=str,
        help=f"Режим неинтерактивной установки: {format_service_codes_help()} или --all",
    )
    parser.add_argument(
        "--uninstall",
        nargs="*",
        type=str,
        help=f"Режим неинтерактивного удаления: {format_service_codes_help()} или --all",
    )
    parser.add_argument(
        "--activate",
        nargs="*",
        type=str,
        help=f"Режим неинтерактивной активации: {format_service_codes_help()} или --all",
    )
    parser.add_argument(
        "--deactivate",
        nargs="*",
        type=str,
        help=f"Режим неинтерактивного отключения: {format_service_codes_help()} или --all",
    )
    parser.add_argument(
        "--status",
        nargs="*",
        type=str,
        help=f"Показать статус сервисов: {format_service_codes_help()} или --all",
    )
    parser.add_argument(
        "--info",
        nargs="*",
        type=str,
        help=f"Показать информацию о сервисах: {format_service_codes_help()} или --all",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Применить указанную non-interactive операцию ко всем сервисам",
    )

    parsed = parser.parse_args(argv)

    for option_name in NON_INTERACTIVE_OPTIONS:
        values = getattr(parsed, option_name)
        if values == [] and not parsed.all:
            parser.error(f"--{option_name} требует коды сервисов или флаг --all")
        if parsed.all and values not in (None, []):
            parser.error(f"--{option_name} нельзя использовать одновременно с кодами и --all")

    return parsed
