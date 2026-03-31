from app.core.service_registry import build_main_menu_items
from app.i18n.locale import t
from app.interfaces.menu.menu_utils import run_menu_loop, show_info_screen


def display_program_info():
    """Отображает информацию о программе и её возможностях"""
    show_info_screen(
        t("main.program_info_title"),
        [
            t("main.program_info_intro"),
            t("main.program_info_services"),
            t("main.program_info_performance"),
            t("main.program_info_security"),
            t("main.program_info_repo"),
        ],
    )


def _exit_program() -> None:
    print(t("common.goodbye"))
    exit()


def run_interactive_script():
    run_menu_loop(
        title=t("main.title"),
        header=t("main.header"),
        items_factory=build_main_menu_items,
        info_handler=display_program_info,
        exit_handler=_exit_program,
        info_label=t("main.info_label"),
        exit_label=t("main.exit_label"),
        invalid_message=t("common.invalid_input"),
    )
