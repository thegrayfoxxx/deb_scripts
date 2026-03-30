"""Тесты для интерактивного главного модуля."""

from unittest.mock import patch

from app.interfaces.interactive.run import run_interactive_script


def _run_main_menu() -> None:
    try:
        run_interactive_script()
    except SystemExit:
        pass


class TestInteractiveRun:
    """Тесты для интерактивного главного модуля."""

    @patch("builtins.input", side_effect=["0"])
    @patch("builtins.print")
    def test_run_interactive_script_exit(self, mock_print, mock_input):
        _run_main_menu()
        mock_print.assert_called_with("👋 До свидания!")

    @patch("builtins.input", side_effect=["00", "any_key", "0"])
    @patch("builtins.print")
    def test_run_interactive_script_display_info_then_exit(self, mock_print, mock_input):
        _run_main_menu()

        printed_texts = [call.args[0] for call in mock_print.call_args_list if call.args]
        assert any("автоматизировать задачи DevOps" in text for text in printed_texts)

    @patch("builtins.input", side_effect=["999", "0"])
    @patch("builtins.print")
    def test_run_interactive_script_invalid_input(self, mock_print, mock_input):
        _run_main_menu()

        printed_texts = [call.args[0] for call in mock_print.call_args_list if call.args]
        assert any("❌ Неверный ввод, попробуйте снова" in text for text in printed_texts)

    @patch("builtins.input", side_effect=["1", "0"])
    @patch("app.interfaces.interactive.ufw.interactive_run")
    @patch("builtins.print")
    def test_run_interactive_script_select_ufw(self, mock_print, mock_ufw_run, mock_input):
        _run_main_menu()
        mock_ufw_run.assert_called_once()

    @patch("builtins.input", side_effect=["2", "0"])
    @patch("app.interfaces.interactive.bbr.interactive_run")
    @patch("builtins.print")
    def test_run_interactive_script_select_bbr(self, mock_print, mock_bbr_run, mock_input):
        _run_main_menu()
        mock_bbr_run.assert_called_once()

    @patch("builtins.input", side_effect=["3", "0"])
    @patch("app.interfaces.interactive.docker.interactive_run")
    @patch("builtins.print")
    def test_run_interactive_script_select_docker(self, mock_print, mock_docker_run, mock_input):
        _run_main_menu()
        mock_docker_run.assert_called_once()

    @patch("builtins.input", side_effect=["4", "0"])
    @patch("app.interfaces.interactive.fail2ban.interactive_run")
    @patch("builtins.print")
    def test_run_interactive_script_select_fail2ban(
        self, mock_print, mock_fail2ban_run, mock_input
    ):
        _run_main_menu()
        mock_fail2ban_run.assert_called_once()

    @patch("builtins.input", side_effect=["5", "0"])
    @patch("app.interfaces.interactive.traffic_guard.interactive_run")
    @patch("builtins.print")
    def test_run_interactive_script_select_traffic_guard(
        self, mock_print, mock_traffic_guard_run, mock_input
    ):
        _run_main_menu()
        mock_traffic_guard_run.assert_called_once()

    @patch("builtins.input", side_effect=["6", "0"])
    @patch("app.interfaces.interactive.uv.interactive_run")
    @patch("builtins.print")
    def test_run_interactive_script_select_uv(self, mock_print, mock_uv_run, mock_input):
        _run_main_menu()
        mock_uv_run.assert_called_once()
