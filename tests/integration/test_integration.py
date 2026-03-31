"""Интеграционные тесты для проверки ключевых контрактов между модулями."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.bbr import BBRService
from app.services.docker import DockerService
from app.services.fail2ban import Fail2BanService
from app.services.traffic_guard import TrafficGuardService
from app.services.ufw import UfwService
from app.services.uv import UVService


@pytest.mark.integration
class TestIntegration:
    """Интеграционные тесты для проверки реальных контрактов между модулями."""

    def test_bbr_service_reads_current_congestion_control_via_runner(self):
        service = BBRService()

        with patch("app.services.bbr.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="cubic\n")

            result = service._get_current_congestion_control()

        assert result == "cubic"
        mock_run.assert_called_once_with(
            ["sysctl", "-n", "net.ipv4.tcp_congestion_control"], check=False
        )

    def test_docker_install_uses_expected_command_flow(self):
        service = DockerService()

        with patch("app.services.docker.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=1, stdout=""),
                MagicMock(returncode=0, stdout=""),
                MagicMock(returncode=0, stdout=""),
                MagicMock(returncode=0, stdout=""),
                MagicMock(returncode=0, stdout=""),
                MagicMock(returncode=0, stdout="Docker version 24.0.5, build ced0996"),
            ]

            result = service.install()

        assert result is True
        mock_run.assert_any_call(["apt", "install", "-y", "curl"], check=False)
        mock_run.assert_any_call(
            ["curl", "-fsSL", "https://get.docker.com", "-o", "get-docker.sh"], check=False
        )
        mock_run.assert_any_call(["sh", "./get-docker.sh"], check=False)

    def test_fail2ban_service_reads_status_via_systemctl_runner(self):
        service = Fail2BanService()

        with patch("app.services.fail2ban.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="active\n")

            result = service._get_service_status()

        assert result == "active"
        mock_run.assert_called_once_with(["systemctl", "is-active", "fail2ban"], check=False)

    def test_uv_service_checks_installation_via_runner(self):
        service = UVService()

        with patch("app.services.uv.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="uv 0.2.4")

            result = service._is_uv_installed()

        assert result is True
        mock_run.assert_called_once_with(service._get_uv_command("--version"), check=False)

    def test_traffic_guard_check_root_uses_effective_uid(self):
        service = TrafficGuardService()

        with patch("os.geteuid", return_value=0) as mock_geteuid:
            result = service._check_root()

        assert result is True
        mock_geteuid.assert_called_once()

    def test_bbr_write_config_file_uses_filesystem_primitives(self):
        service = BBRService()

        with patch("builtins.open") as mock_open, patch("pathlib.Path.mkdir") as mock_mkdir:
            result = service._write_config_file("/tmp/test.conf", "content", "test")

        assert result is True
        mock_mkdir.assert_called_once()
        mock_open.assert_called_once()

    def test_all_services_expose_unified_public_api(self):
        services = [
            UfwService(),
            BBRService(),
            DockerService(),
            Fail2BanService(),
            TrafficGuardService(),
            UVService(),
        ]

        for service in services:
            assert callable(service.install)
            assert callable(service.uninstall)
            assert callable(service.is_installed)
            assert callable(service.get_status)

    def test_ufw_install_runs_package_install_and_safe_baseline(self):
        service = UfwService()

        with (
            patch("os.geteuid", return_value=0),
            patch("app.services.ufw.run") as mock_run,
            patch.object(service, "is_installed", return_value=False),
            patch.object(service, "ensure_safe_baseline", return_value=True) as mock_baseline,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="")

            result = service.install()

        assert result is True
        mock_run.assert_called_once_with(["apt", "install", "-y", "ufw"], check=False)
        mock_baseline.assert_called_once()

    def test_traffic_guard_firewall_setup_uses_ufw_service_when_ufw_is_inactive(self):
        service = TrafficGuardService()

        with (
            patch("app.services.traffic_guard.UfwService") as mock_ufw_class,
            patch("app.services.traffic_guard.run") as mock_run,
        ):
            mock_ufw = mock_ufw_class.return_value
            mock_ufw.enable_with_ssh_only.return_value = True
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="/usr/sbin/ufw"),
                MagicMock(returncode=0, stdout="Status: inactive"),
            ]

            result = service._setup_firewall_safety()

        assert result is True
        mock_ufw.enable_with_ssh_only.assert_called_once()
