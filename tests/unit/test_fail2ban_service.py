"""Тесты для сервиса Fail2Ban."""

from unittest.mock import Mock, mock_open, patch

from app.services.fail2ban import Fail2BanService


class TestFail2BanService:
    """Тесты для сервиса Fail2Ban."""

    def setup_method(self):
        self.service = Fail2BanService()

    @patch("app.services.fail2ban.run")
    def test_get_service_status_success(self, mock_run):
        """Тест успешной проверки статуса службы"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "active"
        mock_run.return_value = mock_result

        result = self.service._get_service_status()
        assert result == "active"

    @patch("app.services.fail2ban.run")
    def test_get_service_status_invalid_response(self, mock_run):
        """Тест проверки статуса службы с недопустимым ответом"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "invalid_status\n"
        mock_run.return_value = mock_result

        result = self.service._get_service_status()
        assert result is None

    @patch("app.services.fail2ban.run")
    def test_is_service_installed_success(self, mock_run):
        """Тест проверки установки службы когда она установлена"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "fail2ban.service                            enabled\n"
        mock_run.return_value = mock_result

        result = self.service._is_service_installed()
        assert result is True

    @patch("app.services.fail2ban.run")
    def test_is_service_installed_not_found(self, mock_run):
        """Тест проверки установки службы когда она не установлена"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        result = self.service._is_service_installed()
        assert result is False

    @patch("app.services.fail2ban.run")
    def test_is_jail_active_success(self, mock_run):
        """Тест проверки активности jail когда он активен"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Status for the sshd jail:\nStatus: Active"
        mock_run.return_value = mock_result

        result = self.service._is_jail_active("sshd")
        assert result is True

    @patch("app.services.fail2ban.run")
    def test_is_jail_active_file_not_found(self, mock_run):
        """Тест проверки активности jail когда команда не найдена"""
        mock_run.side_effect = FileNotFoundError("Command not found")

        result = self.service._is_jail_active("sshd")
        assert result is False

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.mkdir")
    def test_write_config_file_success(self, mock_mkdir, mock_file):
        """Тест успешной записи конфигурационного файла"""
        from pathlib import Path

        result = self.service._write_config_file(
            "/etc/fail2ban/jail.d/sshd.local", "config content", "test config"
        )
        assert result is True
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_file.assert_called_once_with(
            Path("/etc/fail2ban/jail.d/sshd.local"), "w", encoding="utf-8"
        )
        mock_file().write.assert_called_once_with("config content\n")

    @patch("builtins.open")
    def test_write_config_file_permission_error(self, mock_open):
        """Тест записи конфигурационного файла с ошибкой доступа"""
        mock_open.side_effect = PermissionError("Permission denied")

        result = self.service._write_config_file("/tmp/test.conf", "content", "test file")
        assert result is False

    @patch("app.services.fail2ban.time.sleep")
    @patch("app.services.fail2ban.time.time")
    @patch("app.services.fail2ban.Fail2BanService._get_service_status")
    def test_wait_for_service_status_success(self, mock_get_status, mock_time, mock_sleep):
        """Тест ожидания статуса службы с успешным результатом"""
        # Return target status on first call
        mock_get_status.return_value = "active"
        mock_time.side_effect = [0, 0, 0.5]  # start time and check time

        result = self.service._wait_for_service_status("active", max_wait=5, poll_interval=0.5)

        assert result is True
        mock_get_status.assert_called()

    @patch("app.services.fail2ban.time.sleep")
    @patch("app.services.fail2ban.time.time")
    @patch("app.services.fail2ban.Fail2BanService._get_service_status")
    def test_wait_for_service_status_timeout(self, mock_get_status, mock_time, mock_sleep):
        """Тест ожидания статуса службы с таймаутом"""
        mock_get_status.return_value = "inactive"
        # Provide sufficient time values to avoid StopIteration
        mock_time.side_effect = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10] + [i for i in range(11, 40)]

        result = self.service._wait_for_service_status("active", max_wait=2, poll_interval=0.1)

        assert result is False

    @patch("app.services.fail2ban.run")
    def test_get_service_status_command_not_found(self, mock_run):
        """Тест получения статуса службы когда команда не найдена"""
        mock_run.side_effect = FileNotFoundError("Command not found")

        status = self.service._get_service_status()
        assert status is None

    @patch("app.services.fail2ban.run")
    def test_is_service_installed_exception(self, mock_run):
        """Тест проверки установки службы с исключением"""
        mock_run.side_effect = Exception("Test exception")

        result = self.service._is_service_installed()
        assert result is False

    @patch("app.services.fail2ban.run")
    def test_is_jail_active_exception(self, mock_run):
        """Тест проверки активности jail с исключением"""
        mock_run.side_effect = Exception("Test exception")

        result = self.service._is_jail_active("sshd")
        assert result is False
