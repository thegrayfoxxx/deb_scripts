from unittest.mock import Mock, patch

from app.utils.subprocess_utils import is_command_available, run


class TestMainComponents:
    @patch("app.utils.subprocess_utils.subprocess.run")
    def test_run_function_success(self, mock_subprocess_run):
        """Тест успешного выполнения команды через run"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "success output"
        mock_result.stderr = ""
        mock_subprocess_run.return_value = mock_result

        result = run(["echo", "hello"])

        mock_subprocess_run.assert_called_once_with(
            args=["echo", "hello"], check=True, text=True, capture_output=True
        )
        assert result == mock_result

    @patch("app.utils.subprocess_utils.subprocess.run")
    def test_run_function_with_check_false(self, mock_subprocess_run):
        """Тест выполнения команды с check=False"""
        mock_result = Mock()
        mock_result.returncode = 1  # Error code
        mock_result.stdout = ""
        mock_result.stderr = "error message"
        mock_subprocess_run.return_value = mock_result

        result = run(["false"], check=False)

        assert result == mock_result
        assert result.returncode == 1

    @patch("app.utils.subprocess_utils.run")
    def test_is_command_available_success(self, mock_run):
        """Тест проверки доступности команды"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "command version 1.0"
        mock_run.return_value = mock_result

        result = is_command_available("ls")

        mock_run.assert_called_once_with(["ls", "--version"], check=False)
        assert result is True

    @patch("app.utils.subprocess_utils.run")
    def test_is_command_available_failure(self, mock_run):
        """Тест проверки недоступности команды"""
        mock_run.side_effect = FileNotFoundError()

        result = is_command_available("nonexistent_cmd")

        assert result is False
