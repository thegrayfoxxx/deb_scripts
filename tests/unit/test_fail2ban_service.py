"""Тесты для сервиса Fail2Ban."""

from unittest.mock import Mock, mock_open, patch

from app.services.fail2ban import Fail2BanService


class TestFail2BanService:
    """Тесты для сервиса Fail2Ban."""

    def setup_method(self):
        self.service = Fail2BanService()

    @patch("app.services.fail2ban.run")
    def test_get_service_status_success(self, mock_run):
        mock_run.return_value = Mock(returncode=0, stdout="active")

        result = self.service._get_service_status()

        assert result == "active"
        mock_run.assert_called_once_with(["systemctl", "is-active", "fail2ban"], check=False)

    @patch("app.services.fail2ban.run")
    def test_get_service_status_invalid_response(self, mock_run):
        mock_run.return_value = Mock(returncode=0, stdout="invalid_status\n")
        assert self.service._get_service_status() is None

    @patch("app.services.fail2ban.run")
    def test_get_service_status_command_not_found(self, mock_run):
        mock_run.side_effect = FileNotFoundError("Command not found")
        assert self.service._get_service_status() is None

    @patch("app.services.fail2ban.run")
    def test_is_service_installed_success(self, mock_run):
        mock_run.return_value = Mock(
            returncode=0, stdout="fail2ban.service                            enabled\n"
        )

        result = self.service._is_service_installed()

        assert result is True
        mock_run.assert_called_once_with(
            ["systemctl", "list-unit-files", "fail2ban.service"], check=False
        )

    @patch("app.services.fail2ban.run")
    def test_is_service_installed_not_found(self, mock_run):
        mock_run.return_value = Mock(returncode=0, stdout="")
        assert self.service._is_service_installed() is False

    @patch("app.services.fail2ban.run")
    def test_is_service_installed_exception(self, mock_run):
        mock_run.side_effect = Exception("Test exception")
        assert self.service._is_service_installed() is False

    @patch("app.services.fail2ban.run")
    def test_is_jail_active_success(self, mock_run):
        mock_run.return_value = Mock(
            returncode=0, stdout="Status for the sshd jail:\nStatus: Active"
        )

        result = self.service._is_jail_active("sshd")

        assert result is True
        mock_run.assert_called_once_with(["fail2ban-client", "status", "sshd"], check=False)

    @patch("app.services.fail2ban.run")
    def test_is_jail_active_file_not_found(self, mock_run):
        mock_run.side_effect = FileNotFoundError("Command not found")
        assert self.service._is_jail_active("sshd") is False

    @patch("app.services.fail2ban.run")
    def test_is_jail_active_exception(self, mock_run):
        mock_run.side_effect = Exception("Test exception")
        assert self.service._is_jail_active("sshd") is False

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.mkdir")
    def test_write_config_file_success(self, mock_mkdir, mock_file):
        result = self.service._write_config_file(
            "/etc/fail2ban/jail.d/sshd.local", "config content", "test config"
        )

        assert result is True
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        from pathlib import Path

        mock_file.assert_called_once_with(
            Path("/etc/fail2ban/jail.d/sshd.local"), "w", encoding="utf-8"
        )
        mock_file().write.assert_called_once_with("config content\n")

    @patch("builtins.open")
    @patch("pathlib.Path.mkdir")
    def test_write_config_file_permission_error(self, mock_mkdir, mock_open_fn):
        mock_open_fn.side_effect = PermissionError()
        result = self.service._write_config_file(
            "/etc/fail2ban/jail.d/sshd.local", "config content", "test config"
        )
        assert result is False

    @patch("builtins.open")
    @patch("pathlib.Path.mkdir")
    def test_write_config_file_general_error(self, mock_mkdir, mock_open_fn):
        mock_open_fn.side_effect = RuntimeError("boom")
        result = self.service._write_config_file(
            "/etc/fail2ban/jail.d/sshd.local", "config content", "test config"
        )
        assert result is False

    @patch("app.services.fail2ban.time.sleep")
    @patch("app.services.fail2ban.time.time")
    @patch("app.services.fail2ban.Fail2BanService._get_service_status")
    def test_wait_for_service_status_success(self, mock_get_status, mock_time, mock_sleep):
        mock_get_status.return_value = "active"
        mock_time.side_effect = list(range(20))

        result = self.service._wait_for_service_status("active", max_wait=5, poll_interval=0.5)

        assert result is True
        mock_get_status.assert_called()

    @patch("app.services.fail2ban.time.sleep")
    @patch("app.services.fail2ban.time.time")
    @patch("app.services.fail2ban.Fail2BanService._get_service_status")
    def test_wait_for_service_status_timeout(self, mock_get_status, mock_time, mock_sleep):
        mock_get_status.return_value = "inactive"
        mock_time.side_effect = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10] + list(range(11, 40))

        result = self.service._wait_for_service_status("active", max_wait=2, poll_interval=0.1)

        assert result is False

    def test_install_wrapper_delegates_to_install_fail2ban(self):
        with patch.object(self.service, "install_fail2ban", return_value=True) as mock_install:
            result = self.service.install()

        assert result is True
        mock_install.assert_called_once_with()

    def test_uninstall_wrapper_delegates_to_uninstall_fail2ban(self):
        with patch.object(self.service, "uninstall_fail2ban", return_value=True) as mock_uninstall:
            result = self.service.uninstall(confirm=True)

        assert result is True
        mock_uninstall.assert_called_once_with(confirm=True)

    def test_get_status_not_installed(self):
        with patch.object(self.service, "_is_service_installed", return_value=False):
            assert self.service.get_status() == "Fail2Ban: not installed"

    def test_get_status_installed_with_active_jail(self):
        with (
            patch.object(self.service, "_is_service_installed", return_value=True),
            patch.object(self.service, "_get_service_status", return_value="active"),
            patch.object(self.service, "_is_jail_active", return_value=True),
        ):
            status = self.service.get_status()

        assert "Fail2Ban: installed" in status
        assert "Service status: active" in status
        assert "SSH jail 'sshd': active" in status

    def test_is_active_true_when_service_and_jail_are_active(self):
        with (
            patch.object(self.service, "_get_service_status", return_value="active"),
            patch.object(self.service, "_is_jail_active", return_value=True),
        ):
            assert self.service.is_active() is True

    def test_is_active_false_when_jail_is_inactive(self):
        with (
            patch.object(self.service, "_get_service_status", return_value="active"),
            patch.object(self.service, "_is_jail_active", return_value=False),
        ):
            assert self.service.is_active() is False

    def test_is_installed_uses_internal_check(self):
        with patch.object(self.service, "_is_service_installed", return_value=True):
            assert self.service.is_installed() is True

    def test_install_fail2ban_returns_true_when_already_active(self):
        with (
            patch.object(self.service, "_is_service_installed", return_value=True),
            patch.object(self.service, "_get_service_status", return_value="active"),
            patch.object(self.service, "_is_jail_active", return_value=True),
        ):
            result = self.service.install_fail2ban()

        assert result is True

    def test_install_fail2ban_returns_false_when_package_install_fails(self):
        with (
            patch.object(self.service, "_is_service_installed", return_value=False),
            patch("app.services.fail2ban.run") as mock_run,
        ):
            mock_run.return_value = Mock(returncode=1, stdout="")

            result = self.service.install_fail2ban()

        assert result is False
        mock_run.assert_called_once_with(["apt", "install", "fail2ban", "-y"], check=False)

    def test_install_fail2ban_returns_false_when_config_write_fails(self):
        with (
            patch.object(self.service, "_is_service_installed", return_value=False),
            patch("app.services.fail2ban.run") as mock_run,
            patch.object(self.service, "_write_config_file", return_value=False) as mock_write,
        ):
            mock_run.return_value = Mock(returncode=0, stdout="")

            result = self.service.install_fail2ban()

        assert result is False
        mock_write.assert_called_once()

    def test_install_fail2ban_returns_false_when_restart_fails(self):
        with (
            patch.object(self.service, "_is_service_installed", return_value=False),
            patch.object(self.service, "_write_config_file", return_value=True),
            patch("app.services.fail2ban.run") as mock_run,
        ):
            mock_run.side_effect = [
                Mock(returncode=0, stdout=""),
                Mock(returncode=0, stdout=""),
                Mock(returncode=1, stdout=""),
            ]

            result = self.service.install_fail2ban()

        assert result is False

    def test_install_fail2ban_returns_false_when_wait_times_out(self):
        with (
            patch.object(self.service, "_is_service_installed", return_value=False),
            patch.object(self.service, "_write_config_file", return_value=True),
            patch.object(self.service, "_wait_for_service_status", return_value=False),
            patch("app.services.fail2ban.run") as mock_run,
        ):
            mock_run.side_effect = [
                Mock(returncode=0, stdout=""),
                Mock(returncode=0, stdout=""),
                Mock(returncode=0, stdout=""),
            ]

            result = self.service.install_fail2ban()

        assert result is False

    def test_install_fail2ban_returns_false_when_jail_not_active_after_start(self):
        with (
            patch.object(self.service, "_is_service_installed", return_value=False),
            patch.object(self.service, "_write_config_file", return_value=True),
            patch.object(self.service, "_wait_for_service_status", return_value=True),
            patch.object(self.service, "_is_jail_active", return_value=False),
            patch("app.services.fail2ban.run") as mock_run,
        ):
            mock_run.side_effect = [
                Mock(returncode=0, stdout=""),
                Mock(returncode=0, stdout=""),
                Mock(returncode=0, stdout=""),
                Mock(returncode=0, stdout="status output"),
            ]

            result = self.service.install_fail2ban()

        assert result is False

    def test_install_fail2ban_successful_full_flow(self):
        with (
            patch.object(self.service, "_is_service_installed", return_value=False),
            patch.object(self.service, "_write_config_file", return_value=True),
            patch.object(self.service, "_wait_for_service_status", return_value=True),
            patch.object(self.service, "_is_jail_active", return_value=True),
            patch("app.services.fail2ban.run") as mock_run,
        ):
            mock_run.side_effect = [
                Mock(returncode=0, stdout=""),
                Mock(returncode=0, stdout=""),
                Mock(returncode=0, stdout=""),
                Mock(returncode=0, stdout="status output"),
                Mock(returncode=0, stdout="Status for the sshd jail"),
            ]

            result = self.service.install_fail2ban()

        assert result is True

    def test_install_fail2ban_handles_file_not_found(self):
        with (
            patch.object(self.service, "_is_service_installed", return_value=False),
            patch("app.services.fail2ban.run", side_effect=FileNotFoundError("apt")),
        ):
            assert self.service.install_fail2ban() is False

    def test_install_fail2ban_handles_permission_error(self):
        with (
            patch.object(self.service, "_is_service_installed", return_value=False),
            patch("app.services.fail2ban.run", side_effect=PermissionError("denied")),
        ):
            assert self.service.install_fail2ban() is False

    def test_install_fail2ban_handles_general_exception(self):
        with (
            patch.object(self.service, "_is_service_installed", return_value=False),
            patch("app.services.fail2ban.run", side_effect=RuntimeError("boom")),
        ):
            assert self.service.install_fail2ban() is False

    @patch("builtins.input", return_value="n")
    def test_uninstall_fail2ban_cancelled_by_user(self, mock_input):
        assert self.service.uninstall_fail2ban(confirm=True) is True

    def test_uninstall_fail2ban_returns_true_when_not_installed(self):
        with (
            patch.object(self.service, "_is_service_installed", return_value=False),
            patch("app.services.fail2ban.run") as mock_run,
        ):
            result = self.service.uninstall_fail2ban()

        assert result is True
        mock_run.assert_called_once_with(["rm", "-f", self.service.JAIL_CONFIG_PATH], check=False)

    def test_uninstall_fail2ban_successful_full_flow(self):
        with (
            patch.object(self.service, "_is_service_installed", side_effect=[True, False]),
            patch.object(self.service, "_wait_for_service_status", return_value=True),
            patch("app.services.fail2ban.run") as mock_run,
        ):
            mock_run.side_effect = [
                Mock(returncode=0, stdout=""),
                Mock(returncode=0, stdout=""),
                Mock(returncode=0, stdout=""),
                Mock(returncode=0, stdout=""),
            ]

            result = self.service.uninstall_fail2ban()

        assert result is True

    def test_uninstall_fail2ban_returns_true_when_package_already_removed(self):
        with (
            patch.object(self.service, "_is_service_installed", side_effect=[True, False]),
            patch.object(self.service, "_wait_for_service_status", return_value=True),
            patch("app.services.fail2ban.run") as mock_run,
        ):
            mock_run.side_effect = [
                Mock(returncode=1, stdout=""),
                Mock(returncode=1, stdout=""),
                Mock(returncode=100, stdout=""),
                Mock(returncode=0, stdout=""),
            ]

            result = self.service.uninstall_fail2ban()

        assert result is True

    def test_uninstall_fail2ban_returns_false_when_still_installed_after_removal(self):
        with (
            patch.object(self.service, "_is_service_installed", side_effect=[True, True]),
            patch.object(self.service, "_wait_for_service_status", return_value=True),
            patch("app.services.fail2ban.run") as mock_run,
        ):
            mock_run.side_effect = [
                Mock(returncode=1, stdout=""),
                Mock(returncode=1, stdout=""),
                Mock(returncode=1, stdout=""),
                Mock(returncode=0, stdout=""),
            ]

            result = self.service.uninstall_fail2ban()

        assert result is False

    def test_uninstall_fail2ban_handles_file_not_found(self):
        with patch.object(self.service, "_is_service_installed", side_effect=FileNotFoundError):
            assert self.service.uninstall_fail2ban() is True

    def test_uninstall_fail2ban_handles_permission_error(self):
        with (
            patch.object(self.service, "_is_service_installed", return_value=True),
            patch("app.services.fail2ban.run", side_effect=PermissionError("denied")),
        ):
            assert self.service.uninstall_fail2ban() is False

    def test_uninstall_fail2ban_handles_general_exception(self):
        with (
            patch.object(self.service, "_is_service_installed", return_value=True),
            patch("app.services.fail2ban.run", side_effect=RuntimeError("boom")),
        ):
            assert self.service.uninstall_fail2ban() is False
