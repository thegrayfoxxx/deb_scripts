"""Тесты для утилит запуска subprocess."""

from unittest.mock import Mock, patch

from app.core.subprocess import is_command_available, run


class TestSubprocessUtils:
    """Тесты для утилит запуска subprocess."""

    @patch("app.core.subprocess.subprocess.run")
    def test_run_success_with_check_true(self, mock_subprocess_run):
        """Тест запуска команды с check=True при успешном выполнении"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess_run.return_value = mock_result

        result = run(["echo", "hello"], check=True)

        assert result == mock_result
        mock_subprocess_run.assert_called_once_with(
            args=["echo", "hello"], check=True, text=True, capture_output=True
        )

    @patch("app.core.subprocess.subprocess.run")
    def test_run_with_check_false_and_success(self, mock_subprocess_run):
        """Тест запуска команды с check=False при успешном выполнении"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess_run.return_value = mock_result

        result = run(["echo", "hello"], check=False)

        assert result == mock_result
        mock_subprocess_run.assert_called_once_with(
            args=["echo", "hello"], check=False, text=True, capture_output=True
        )

    @patch("app.core.subprocess.subprocess.run")
    def test_run_with_check_false_and_failure(self, mock_subprocess_run):
        """Тест запуска команды с check=False при неудачном выполнении"""
        mock_error = Mock()
        mock_error.returncode = 1
        mock_error.stdout = ""
        mock_error.stderr = "error message"
        mock_subprocess_run.side_effect = Mock(side_effect=Exception())
        # For the exception scenario, we'll make subprocess.run raise CalledProcessError
        from subprocess import CalledProcessError

        called_process_error = CalledProcessError(1, ["echo", "hello"])
        called_process_error.stdout = "output"
        called_process_error.stderr = "error"
        mock_subprocess_run.side_effect = called_process_error

        # We need to handle this carefully - let's recreate the scenario properly
        with patch("app.core.subprocess.subprocess.run") as mock_run:
            from subprocess import CalledProcessError

            error = CalledProcessError(1, ["echo", "hello"])
            error.stdout = "output"
            error.stderr = "error"
            mock_run.side_effect = error

            result = run(["echo", "hello"], check=False)

            assert hasattr(result, "returncode")
            assert result.returncode == 1

    @patch("app.core.subprocess.subprocess.run")
    def test_run_with_additional_kwargs(self, mock_subprocess_run):
        """Тест запуска команды с дополнительными параметрами"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess_run.return_value = mock_result

        run(["echo", "hello"], check=True, timeout=10)

        mock_subprocess_run.assert_called_once_with(
            args=["echo", "hello"], check=True, text=True, capture_output=True, timeout=10
        )

    def test_is_command_available_success(self):
        """Тест проверки доступности команды при её наличии"""
        with patch("app.core.subprocess.run") as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            result = is_command_available("ls")

            assert result is True
            mock_run.assert_called_once_with(["ls", "--version"], check=False)

    def test_is_command_available_failure_returncode(self):
        """Тест проверки доступности команды при её отсутствии (ненулевой код возврата)"""
        with patch("app.core.subprocess.run") as mock_run:
            mock_result = Mock()
            mock_result.returncode = 1
            mock_run.return_value = mock_result

            result = is_command_available("nonexistent_cmd")

            assert result is False
            mock_run.assert_called_once_with(["nonexistent_cmd", "--version"], check=False)

    def test_is_command_available_file_not_found(self):
        """Тест проверки доступности команды при её отсутствии (FileNotFoundError)"""
        with patch("app.core.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("Command not found")

            result = is_command_available("nonexistent_cmd")

            assert result is False
            mock_run.assert_called_once_with(["nonexistent_cmd", "--version"], check=False)

    @patch("app.core.subprocess.subprocess.run")
    def test_run_exception_propagates_when_check_true(self, mock_subprocess_run):
        """Тест что исключение propagates при check=True"""
        from subprocess import CalledProcessError

        error = CalledProcessError(1, ["echo", "hello"])
        mock_subprocess_run.side_effect = error

        try:
            run(["echo", "hello"], check=True)
            assert False, "Should have raised CalledProcessError"
        except CalledProcessError:
            pass

    @patch("app.core.subprocess.subprocess.run")
    def test_run_handles_text_and_capture_output_params(self, mock_subprocess_run):
        """Тест что run правильно передает параметры text и capture_output"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess_run.return_value = mock_result

        run(["echo", "hello"])

        mock_subprocess_run.assert_called_once_with(
            args=["echo", "hello"], check=True, text=True, capture_output=True
        )
