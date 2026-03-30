from unittest.mock import Mock, patch

from app.services.bbr import BBRService
from app.services.docker import DockerService
from app.services.fail2ban import Fail2BanService
from app.services.traffic_guard import TrafficGuardService
from app.services.ufw import UfwService
from app.services.uv import UVService


def test_bbr_get_status_enabled():
    service = BBRService()

    with (
        patch.object(service, "_get_current_congestion_control", return_value="bbr"),
        patch.object(service, "_is_bbr_module_loaded", return_value=True),
    ):
        status = service.get_status()

    assert "BBR: enabled" in status


def test_docker_get_status_installed():
    service = DockerService()

    with patch.object(service, "_get_docker_version", return_value="Docker version 24.0.5"):
        status = service.get_status()

    assert "Docker: installed" in status
    assert "Docker version 24.0.5" in status


def test_fail2ban_get_status_not_installed():
    service = Fail2BanService()

    with patch.object(service, "_is_service_installed", return_value=False):
        status = service.get_status()

    assert status == "Fail2Ban: not installed"


def test_trafficguard_get_status_installed():
    service = TrafficGuardService()

    with (
        patch.object(service, "_is_trafficguard_installed", return_value=True),
        patch.object(service, "_get_service_status", return_value="active"),
        patch("app.services.traffic_guard.run") as mock_run,
    ):
        mock_run.return_value = Mock(returncode=0, stdout="TrafficGuard v1.0\n")
        status = service.get_status()

    assert "TrafficGuard: installed" in status
    assert "TrafficGuard v1.0" in status
    assert "active" in status


def test_uv_get_status_installed():
    service = UVService()

    with (
        patch.object(service, "_is_uv_installed", return_value=True),
        patch.object(service, "_is_path_configured", return_value=True),
        patch("app.services.uv.run") as mock_run,
    ):
        mock_run.return_value = Mock(returncode=0, stdout="uv 0.7.0\n")
        status = service.get_status()

    assert "uv: installed" in status
    assert "uv 0.7.0" in status
    assert "PATH configured: yes" in status


def test_ufw_is_active_uses_internal_check():
    service = UfwService()

    with patch.object(service, "_is_active", return_value=True):
        assert service.is_active() is True
