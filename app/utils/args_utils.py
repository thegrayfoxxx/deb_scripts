import argparse
import sys


def parse_args():
    parser = argparse.ArgumentParser(
        description="Инфо", formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "--mode", choices=["dev", "prod"], default="prod", help="Режим работы приложения"
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
