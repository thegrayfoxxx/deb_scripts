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
        patch.object(service, "is_installed", return_value=True),
    ):
        status = service.get_status()

    assert "Статус установки: 🟢 установлен" in status
    assert "Статус активации: 🟢 активирован" in status
    assert "Текущий алгоритм перегрузки: bbr" in status


def test_docker_get_status_installed():
    service = DockerService()

    with patch.object(service, "_get_docker_version", return_value="Docker version 24.0.5"):
        status = service.get_status()

    assert "Статус установки: 🟢 установлен" in status
    assert "Версия Docker: Docker version 24.0.5" in status


def test_fail2ban_get_status_not_installed():
    service = Fail2BanService()

    with patch.object(service, "_is_service_installed", return_value=False):
        status = service.get_status()

    assert "Статус установки: 🔴 не установлен" in status
    assert "Статус активации: 🔴 не активирован" in status


def test_trafficguard_get_status_installed():
    service = TrafficGuardService()

    with (
        patch.object(service, "_is_trafficguard_installed", return_value=True),
        patch.object(service, "_get_service_status", return_value="active"),
        patch("app.services.traffic_guard.run") as mock_run,
    ):
        mock_run.return_value = Mock(returncode=0, stdout="TrafficGuard v1.0\n")
        status = service.get_status()

    assert "Статус установки: 🟢 установлен" in status
    assert "Версия TrafficGuard: TrafficGuard v1.0" in status
    assert "Состояние службы: active" in status


def test_uv_get_status_installed():
    service = UVService()

    with (
        patch.object(service, "_is_uv_installed", return_value=True),
        patch.object(service, "_is_path_configured", return_value=True),
        patch("app.services.uv.run") as mock_run,
    ):
        mock_run.return_value = Mock(returncode=0, stdout="uv 0.7.0\n")
        status = service.get_status()

    assert "Статус установки: 🟢 установлен" in status
    assert "Версия uv: uv 0.7.0" in status
    assert "PATH настроен: да" in status


def test_ufw_is_active_uses_internal_check():
    service = UfwService()

    with patch.object(service, "_is_active", return_value=True):
        assert service.is_active() is True


def test_ufw_get_status_does_not_call_is_active_recursively():
    service = UfwService()

    with (
        patch.object(service, "is_installed", return_value=True),
        patch.object(service, "is_active", side_effect=AssertionError("recursive call")),
        patch("app.services.ufw.run") as mock_run,
    ):
        mock_run.return_value = Mock(returncode=0, stdout="Status: inactive\n")
        status = service.get_status()

    assert "Статус установки: 🟢 установлен" in status
    assert "Статус активации: 🔴 не активирован" in status
