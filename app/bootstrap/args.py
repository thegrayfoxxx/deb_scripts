import argparse
import sys

from app.core.service_registry import format_service_codes_help
from app.i18n.locale import DEFAULT_LOCALE, SUPPORTED_LOCALES, translate

NON_INTERACTIVE_OPTIONS = ("install", "uninstall", "activate", "deactivate", "status", "info")


def _detect_requested_language(argv: list[str] | None = None) -> str:
    arguments = list(sys.argv[1:] if argv is None else argv)

    for index, value in enumerate(arguments):
        if value == "--lang" and index + 1 < len(arguments):
            return arguments[index + 1].lower()
        if value.startswith("--lang="):
            return value.split("=", 1)[1].lower()

    return DEFAULT_LOCALE


def _build_parser(language: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=translate("main.description", locale=language),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "--lang",
        choices=list(SUPPORTED_LOCALES),
        default=DEFAULT_LOCALE,
        help=translate("main.lang_help", locale=language),
    )
    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error"],
        default="info",
        help=translate("main.log_level_help", locale=language),
    )
    parser.add_argument(
        "--install",
        nargs="*",
        type=str,
        help=translate(
            "args.install_help",
            locale=language,
            codes=format_service_codes_help(),
        ),
    )
    parser.add_argument(
        "--uninstall",
        nargs="*",
        type=str,
        help=translate(
            "args.uninstall_help",
            locale=language,
            codes=format_service_codes_help(),
        ),
    )
    parser.add_argument(
        "--activate",
        nargs="*",
        type=str,
        help=translate(
            "args.activate_help",
            locale=language,
            codes=format_service_codes_help(),
        ),
    )
    parser.add_argument(
        "--deactivate",
        nargs="*",
        type=str,
        help=translate(
            "args.deactivate_help",
            locale=language,
            codes=format_service_codes_help(),
        ),
    )
    parser.add_argument(
        "--status",
        nargs="*",
        type=str,
        help=translate(
            "args.status_help",
            locale=language,
            codes=format_service_codes_help(),
        ),
    )
    parser.add_argument(
        "--info",
        nargs="*",
        type=str,
        help=translate(
            "args.info_help",
            locale=language,
            codes=format_service_codes_help(),
        ),
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help=translate("args.all_help", locale=language),
    )
    return parser


def parse_args(argv: list[str] | None = None):
    parser = _build_parser(_detect_requested_language(argv))

    parsed = parser.parse_args(argv)

    for option_name in NON_INTERACTIVE_OPTIONS:
        values = getattr(parsed, option_name)
        if values == [] and not parsed.all:
            parser.error(
                translate("args.error_codes_or_all", locale=parsed.lang, option_name=option_name)
            )
        if parsed.all and values not in (None, []):
            parser.error(
                translate("args.error_codes_with_all", locale=parsed.lang, option_name=option_name)
            )

    return parsed
