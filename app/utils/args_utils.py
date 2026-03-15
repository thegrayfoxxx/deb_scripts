import argparse


def parse_args():
    parser = argparse.ArgumentParser(
        description="Инфо", formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "--mode", choices=["dev", "prod"], default="prod", help="Режим работы приложения"
    )

    return parser.parse_args()


app_args = parse_args()
