from pathlib import Path
from unittest.mock import Mock, mock_open, patch

from app.services.fail2ban import Fail2BanService


class TestFail2BanService:
    def setup_method(self):
        self.service = Fail2BanService()

    @patch("app.services.fail2ban.run")
    def test_get_service_status_success(self, mock_run):
        """Тест успешной проверки статуса службы"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "active\n"
        mock_run.return_value = mock_result

        result = self.service._get_service_status()
        assert result == "active"
        mock_run.assert_called_once_with(["systemctl", "is-active", "fail2ban"], check=False)

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
        """Тест успешной проверки установки службы"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "fail2ban.service                            enabled\n"
        mock_run.return_value = mock_result

        assert self.service._is_service_installed() is True
        mock_run.assert_called_once_with(
            ["systemctl", "list-unit-files", "fail2ban.service"], check=False
        )

    @patch("app.services.fail2ban.run")
    def test_is_service_installed_not_found(self, mock_run):
        """Тест проверки установки службы когда она не установлена"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "other.service                              enabled\n"
        mock_run.return_value = mock_result

        assert self.service._is_service_installed() is False

    @patch("app.services.fail2ban.run")
    def test_is_jail_active_success(self, mock_run):
        """Тест успешной проверки активности jail"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = (
            "Status for jail 'sshd':\n  |- Filter: \n  |- Action: \n  `- Status: ACTIVE"
        )
        mock_run.return_value = mock_result

        assert self.service._is_jail_active("sshd") is True
        mock_run.assert_called_once_with(["fail2ban-client", "status", "sshd"], check=False)

    @patch("app.services.fail2ban.run")
    def test_is_jail_active_file_not_found(self, mock_run):
        """Тест проверки активности jail с FileNotFoundError"""
        mock_run.side_effect = FileNotFoundError()

        assert self.service._is_jail_active("sshd") is False

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.mkdir")
    def test_write_config_file_success(self, mock_mkdir, mock_file):
        """Тест успешной записи конфигурационного файла"""
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
    @patch("pathlib.Path.mkdir")
    def test_write_config_file_permission_error(self, mock_mkdir, mock_file):
        """Тест записи конфигурационного файла с PermissionError"""
        mock_file.side_effect = PermissionError()

        result = self.service._write_config_file(
            "/etc/fail2ban/jail.d/sshd.local", "config content", "test config"
        )

        assert result is False

    @patch("app.services.fail2ban.time.sleep")
    @patch("app.services.fail2ban.time.time")
    @patch("app.services.fail2ban.Fail2BanService._get_service_status")
    def test_wait_for_service_status_success(self, mock_get_status, mock_time, mock_sleep):
        """Тест ожидания статуса службы с успешным результатом"""
        # Return target status on second call
        mock_get_status.side_effect = ["inactive", "active", "active"]
        # Set up time mocks: start time, then increasing times
        mock_time.side_effect = [0, 0, 1, 1, 2, 2]  # time.time called twice per loop iteration

        result = self.service._wait_for_service_status("active", max_wait=5, poll_interval=1)

        assert result is True
        assert mock_get_status.call_count >= 1  # At least one call

    @patch("app.services.fail2ban.time.sleep")
    @patch("app.services.fail2ban.time.time")
    @patch("app.services.fail2ban.Fail2BanService._get_service_status")
    def test_wait_for_service_status_timeout(self, mock_get_status, mock_time, mock_sleep):
        """Тест ожидания статуса службы с таймаутом"""
        mock_get_status.return_value = "inactive"
        # Simulate time passing for timeout - need double the calls due to two time.time() calls per loop
        mock_time.side_effect = [0, 0, 1, 1, 2, 2, 35, 35]  # Exceeds max_wait of 30

        result = self.service._wait_for_service_status("active", max_wait=30, poll_interval=1)

        assert result is False

    @patch("app.services.fail2ban.Fail2BanService._is_service_installed")
    @patch("app.services.fail2ban.Fail2BanService._get_service_status")
    @patch("app.services.fail2ban.Fail2BanService._is_jail_active")
    def test_install_fail2ban_already_installed_and_running(
        self, mock_is_jail_active, mock_get_status, mock_is_installed
    ):
        """Тест установки fail2ban когда он уже установлен и запущен"""
        mock_is_installed.return_value = True
        mock_get_status.return_value = "active"
        mock_is_jail_active.return_value = True

        self.service.install_fail2ban()

        # Only the initial checks should happen
        mock_is_installed.assert_called_once()
        mock_get_status.assert_called_once()
        mock_is_jail_active.assert_called_once_with("sshd")

    @patch("app.services.fail2ban.update_os")
    @patch("app.services.fail2ban.Fail2BanService._is_service_installed")
    @patch("app.services.fail2ban.Fail2BanService._get_service_status")
    @patch("app.services.fail2ban.Fail2BanService._is_jail_active")
    @patch("app.services.fail2ban.Fail2BanService._write_config_file")
    @patch("app.services.fail2ban.Fail2BanService._wait_for_service_status")
    @patch("app.services.fail2ban.run")
    def test_install_fail2ban_first_time(
        self,
        mock_run,
        mock_wait_for_status,
        mock_write_config,
        mock_is_jail_active,
        mock_get_status,
        mock_is_installed,
        mock_update_os,
    ):
        """Тест установки fail2ban при первом запуске"""
        # Simulate that fail2ban is not installed initially
        mock_is_installed.return_value = False
        # After installation and restart, it becomes active
        mock_get_status.return_value = "active"
        mock_is_jail_active.return_value = True
        mock_write_config.return_value = True
        mock_wait_for_status.return_value = True

        side_effects = [
            Mock(returncode=0, stdout=""),  # apt install
            Mock(returncode=0, stdout=""),  # systemctl enable
            Mock(returncode=0, stdout=""),  # systemctl restart
            Mock(returncode=0, stdout="status output"),  # systemctl status
            Mock(returncode=0, stdout="jail status output"),  # fail2ban-client status
        ]
        mock_run.side_effect = side_effects

        self.service.install_fail2ban()

        # Verify key actions happened
        mock_update_os.assert_called_once()
        assert mock_run.call_count >= 3  # apt install, systemctl enable, systemctl restart
        mock_write_config.assert_called_once()
        mock_wait_for_status.assert_called_once_with("active", max_wait=30)

    @patch("app.services.fail2ban.Fail2BanService._is_service_installed")
    @patch("app.services.fail2ban.run")
    def test_uninstall_fail2ban_not_installed(self, mock_run, mock_is_installed):
        """Тест удаления fail2ban когда он не установлен"""
        mock_is_installed.return_value = False

        self.service.uninstall_fail2ban()

        # Should check if installed first
        mock_is_installed.assert_called_once()
        # And try to remove config file regardless
        mock_run.assert_called_once_with(
            ["rm", "-f", "/etc/fail2ban/jail.d/sshd.local"], check=False
        )

    @patch("app.services.fail2ban.Fail2BanService._is_service_installed")
    @patch("app.services.fail2ban.Fail2BanService._wait_for_service_status")
    @patch("app.services.fail2ban.run")
    def test_uninstall_fail2ban_installed(self, mock_run, mock_wait_for_status, mock_is_installed):
        """Тест удаления fail2ban когда он установлен"""
        mock_is_installed.return_value = True
        mock_wait_for_status.return_value = True

        side_effects = [
            Mock(returncode=0, stdout=""),  # systemctl stop
            Mock(returncode=0, stdout=""),  # systemctl disable
            Mock(returncode=0, stdout=""),  # apt remove
            Mock(returncode=0, stdout=""),  # rm config
        ]
        mock_run.side_effect = side_effects

        self.service.uninstall_fail2ban()

        # Verify that the critical steps occurred
        assert mock_run.call_count >= 4  # stop, disable, remove, rm config
        mock_wait_for_status.assert_called_once_with("inactive", max_wait=15)
