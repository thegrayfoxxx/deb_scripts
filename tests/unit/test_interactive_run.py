"""Тесты для интерактивного главного модуля."""

from unittest.mock import MagicMock, patch

from app.interfaces.interactive.menu_utils import MenuItem
from app.interfaces.interactive.run import run_interactive_script


def _run_main_menu() -> None:
    try:
        run_interactive_script()
    except SystemExit:
        pass


def _menu_items_with_actions() -> tuple[list[MenuItem], dict[str, MagicMock]]:
    actions = {code: MagicMock() for code in ["1", "2", "3", "4", "5", "6"]}
    items = [
        MenuItem(key=code, label=f"{code} - service", action=action)
        for code, action in actions.items()
    ]
    return items, actions


class TestInteractiveRun:
    """Тесты для интерактивного главного модуля."""

    @patch("builtins.input", side_effect=["0"])
    @patch("builtins.print")
    def test_run_interactive_script_exit(self, mock_print, mock_input):
        _run_main_menu()
        mock_print.assert_called_with("👋 До свидания!")

    @patch("builtins.input", side_effect=["00", "any_key", "0"])
    @patch("builtins.print")
    def test_run_interactive_script_display_info_then_exit(
        self, mock_print, mock_input
    ):
        _run_main_menu()

        printed_texts = [
            call.args[0] for call in mock_print.call_args_list if call.args
        ]
        assert any("автоматизировать задачи DevOps" in text for text in printed_texts)

    @patch("builtins.input", side_effect=["999", "0"])
    @patch("builtins.print")
    def test_run_interactive_script_invalid_input(self, mock_print, mock_input):
        _run_main_menu()

        printed_texts = [
            call.args[0] for call in mock_print.call_args_list if call.args
        ]
        assert any(
            "❌ Неверный ввод, попробуйте снова" in text for text in printed_texts
        )

    @patch("builtins.input", side_effect=["1", "0"])
    @patch("builtins.print")
    def test_run_interactive_script_select_ufw(self, mock_print, mock_input):
        items, actions = _menu_items_with_actions()

        with patch(
            "app.interfaces.interactive.run.build_main_menu_items", return_value=items
        ):
            _run_main_menu()

        actions["1"].assert_called_once()

    @patch("builtins.input", side_effect=["2", "0"])
    @patch("builtins.print")
    def test_run_interactive_script_select_bbr(self, mock_print, mock_input):
        items, actions = _menu_items_with_actions()

        with patch(
            "app.interfaces.interactive.run.build_main_menu_items", return_value=items
        ):
            _run_main_menu()

        actions["2"].assert_called_once()

    @patch("builtins.input", side_effect=["3", "0"])
    @patch("builtins.print")
    def test_run_interactive_script_select_docker(self, mock_print, mock_input):
        items, actions = _menu_items_with_actions()

        with patch(
            "app.interfaces.interactive.run.build_main_menu_items", return_value=items
        ):
            _run_main_menu()

        actions["3"].assert_called_once()

    @patch("builtins.input", side_effect=["4", "0"])
    @patch("builtins.print")
    def test_run_interactive_script_select_fail2ban(self, mock_print, mock_input):
        items, actions = _menu_items_with_actions()

        with patch(
            "app.interfaces.interactive.run.build_main_menu_items", return_value=items
        ):
            _run_main_menu()

        actions["4"].assert_called_once()

    @patch("builtins.input", side_effect=["5", "0"])
    @patch("builtins.print")
    def test_run_interactive_script_select_traffic_guard(self, mock_print, mock_input):
        items, actions = _menu_items_with_actions()

        with patch(
            "app.interfaces.interactive.run.build_main_menu_items", return_value=items
        ):
            _run_main_menu()

        actions["5"].assert_called_once()

    @patch("builtins.input", side_effect=["6", "0"])
    @patch("builtins.print")
    def test_run_interactive_script_select_uv(self, mock_print, mock_input):
        items, actions = _menu_items_with_actions()

        with patch(
            "app.interfaces.interactive.run.build_main_menu_items", return_value=items
        ):
            _run_main_menu()

        actions["6"].assert_called_once()
