from unittest.mock import MagicMock, patch

from app.interfaces.cli.non_interactive import run_non_interactive_commands


def test_run_non_interactive_install_bbr():
    """Test non-interactive BBR installation"""
    # Create a mock instance
    mock_bbr_instance = MagicMock()

    # Create test args
    class TestArgs:
        install = ["2"]
        uninstall = None

    args = TestArgs()

    # Patch the BBR service to return our mock
    with patch("app.interfaces.cli.non_interactive.BBRService") as mock_bbr_service:
        mock_bbr_service.return_value = mock_bbr_instance

        result = run_non_interactive_commands(args)

        assert result is True
        mock_bbr_instance.install.assert_called_once()


def test_run_non_interactive_install_docker():
    """Test non-interactive Docker installation"""
    # Create a mock instance
    mock_docker_instance = MagicMock()

    # Create test args
    class TestArgs:
        install = ["3"]
        uninstall = None

    args = TestArgs()

    # Patch the Docker service to return our mock
    with patch("app.interfaces.cli.non_interactive.DockerService") as mock_docker_service:
        mock_docker_service.return_value = mock_docker_instance

        result = run_non_interactive_commands(args)

        assert result is True
        mock_docker_instance.install.assert_called_once()


def test_run_non_interactive_uninstall_fail2ban():
    """Test non-interactive Fail2Ban uninstallation"""
    # Create a mock instance
    mock_f2b_instance = MagicMock()

    # Create test args
    class TestArgs:
        install = None
        uninstall = ["4"]

    args = TestArgs()

    # Patch the Fail2Ban service to return our mock
    with patch("app.interfaces.cli.non_interactive.Fail2BanService") as mock_f2b_service:
        mock_f2b_service.return_value = mock_f2b_instance

        result = run_non_interactive_commands(args)

        assert result is True
        mock_f2b_instance.uninstall.assert_called_once()


def test_run_non_interactive_install_trafficguard():
    """Test non-interactive TrafficGuard installation"""
    # Create a mock instance
    mock_tg_instance = MagicMock()

    # Create test args
    class TestArgs:
        install = ["5"]
        uninstall = None

    args = TestArgs()

    # Patch the TrafficGuard service to return our mock
    with patch("app.interfaces.cli.non_interactive.TrafficGuardService") as mock_tg_service:
        mock_tg_service.return_value = mock_tg_instance

        result = run_non_interactive_commands(args)

        assert result is True
        mock_tg_instance.install.assert_called_once()


def test_run_non_interactive_install_uv():
    """Test non-interactive UV installation"""
    # Create a mock instance
    mock_uv_instance = MagicMock()

    # Create test args
    class TestArgs:
        install = ["6"]
        uninstall = None

    args = TestArgs()

    # Patch the UV service to return our mock
    with patch("app.interfaces.cli.non_interactive.UVService") as mock_uv_service:
        mock_uv_service.return_value = mock_uv_instance

        result = run_non_interactive_commands(args)

        assert result is True
        mock_uv_instance.install.assert_called_once()


def test_run_non_interactive_uninstall_multiple_services():
    """Test non-interactive uninstallation of multiple services"""
    # Create mock instances
    mock_ufw_instance = MagicMock()
    mock_bbr_instance = MagicMock()
    mock_docker_instance = MagicMock()

    # Create test args
    class TestArgs:
        install = None
        uninstall = ["2", "3"]

    args = TestArgs()

    # Patch the services to return our mocks
    with (
        patch("app.interfaces.cli.non_interactive.UfwService") as mock_ufw_service,
        patch("app.interfaces.cli.non_interactive.BBRService") as mock_bbr_service,
        patch("app.interfaces.cli.non_interactive.DockerService") as mock_docker_service,
    ):
        mock_ufw_service.return_value = mock_ufw_instance
        mock_bbr_service.return_value = mock_bbr_instance
        mock_docker_service.return_value = mock_docker_instance

        result = run_non_interactive_commands(args)

        assert result is True
        mock_bbr_instance.uninstall.assert_called_once()
        mock_docker_instance.uninstall.assert_called_once()


def test_run_non_interactive_install_multiple_services():
    """Test non-interactive installation of multiple services"""
    # Create mock instances
    mock_ufw_instance = MagicMock()
    mock_bbr_instance = MagicMock()
    mock_docker_instance = MagicMock()

    # Create test args
    class TestArgs:
        install = ["2", "3"]
        uninstall = None

    args = TestArgs()

    # Patch the services to return our mocks
    with (
        patch("app.interfaces.cli.non_interactive.UfwService") as mock_ufw_service,
        patch("app.interfaces.cli.non_interactive.BBRService") as mock_bbr_service,
        patch("app.interfaces.cli.non_interactive.DockerService") as mock_docker_service,
    ):
        mock_ufw_service.return_value = mock_ufw_instance
        mock_bbr_service.return_value = mock_bbr_instance
        mock_docker_service.return_value = mock_docker_instance

        result = run_non_interactive_commands(args)

        assert result is True
        mock_bbr_instance.install.assert_called_once()
        mock_docker_instance.install.assert_called_once()


def test_run_non_interactive_mixed_operations():
    """Test non-interactive mixed install and uninstall operations"""
    # Create mock instances
    mock_ufw_instance = MagicMock()
    mock_bbr_instance = MagicMock()
    mock_docker_instance = MagicMock()

    # Create test args
    class TestArgs:
        install = ["2"]  # Install BBR
        uninstall = ["3"]  # Uninstall Docker

    args = TestArgs()

    # Patch the services to return our mocks
    with (
        patch("app.interfaces.cli.non_interactive.UfwService") as mock_ufw_service,
        patch("app.interfaces.cli.non_interactive.BBRService") as mock_bbr_service,
        patch("app.interfaces.cli.non_interactive.DockerService") as mock_docker_service,
    ):
        mock_ufw_service.return_value = mock_ufw_instance
        mock_bbr_service.return_value = mock_bbr_instance
        mock_docker_service.return_value = mock_docker_instance

        result = run_non_interactive_commands(args)

        assert result is True
        mock_bbr_instance.install.assert_called_once()
        mock_docker_instance.uninstall.assert_called_once()


def test_run_non_interactive_invalid_service_code_install():
    """Test non-interactive installation with invalid service code"""

    # Create test args
    class TestArgs:
        install = ["99"]  # Invalid service code
        uninstall = None

    args = TestArgs()

    # Should not crash with invalid code
    with patch("app.interfaces.cli.non_interactive.logger") as mock_logger:
        result = run_non_interactive_commands(args)

        assert result is False
        mock_logger.error.assert_called_with("❌ Неизвестный код сервиса для установки: 99")


def test_run_non_interactive_invalid_service_code_uninstall():
    """Test non-interactive uninstallation with invalid service code"""

    # Create test args
    class TestArgs:
        install = None
        uninstall = ["99"]  # Invalid service code

    args = TestArgs()

    # Should not crash with invalid code
    with patch("app.interfaces.cli.non_interactive.logger") as mock_logger:
        result = run_non_interactive_commands(args)

        assert result is False
        mock_logger.error.assert_called_with("❌ Неизвестный код сервиса для удаления: 99")


def test_run_non_interactive_no_operations():
    """Test non-interactive mode with no operations specified"""

    # Create test args
    class TestArgs:
        install = None
        uninstall = None

    args = TestArgs()

    result = run_non_interactive_commands(args)
    assert result is True


def test_run_non_interactive_all_services():
    """Test non-interactive installation of all services"""
    # Create mock instances
    mock_ufw_instance = MagicMock()
    mock_bbr_instance = MagicMock()
    mock_docker_instance = MagicMock()
    mock_f2b_instance = MagicMock()
    mock_tg_instance = MagicMock()
    mock_uv_instance = MagicMock()

    # Create test args
    class TestArgs:
        install = ["1", "2", "3", "4", "5", "6"]
        uninstall = None

    args = TestArgs()

    # Patch all services to return our mocks
    with (
        patch("app.interfaces.cli.non_interactive.UfwService") as mock_ufw_service,
        patch("app.interfaces.cli.non_interactive.BBRService") as mock_bbr_service,
        patch("app.interfaces.cli.non_interactive.DockerService") as mock_docker_service,
        patch("app.interfaces.cli.non_interactive.Fail2BanService") as mock_f2b_service,
        patch("app.interfaces.cli.non_interactive.TrafficGuardService") as mock_tg_service,
        patch("app.interfaces.cli.non_interactive.UVService") as mock_uv_service,
    ):
        mock_ufw_service.return_value = mock_ufw_instance
        mock_bbr_service.return_value = mock_bbr_instance
        mock_docker_service.return_value = mock_docker_instance
        mock_f2b_service.return_value = mock_f2b_instance
        mock_tg_service.return_value = mock_tg_instance
        mock_uv_service.return_value = mock_uv_instance

        result = run_non_interactive_commands(args)

        assert result is True
        mock_ufw_instance.install.assert_called_once()
        mock_bbr_instance.install.assert_called_once()
        mock_docker_instance.install.assert_called_once()
        mock_f2b_instance.install.assert_called_once()
        mock_tg_instance.install.assert_called_once()
        mock_uv_instance.install.assert_called_once()


def test_run_non_interactive_uninstall_all_services():
    """Test non-interactive uninstallation of all services"""
    # Create mock instances
    mock_ufw_instance = MagicMock()
    mock_bbr_instance = MagicMock()
    mock_docker_instance = MagicMock()
    mock_f2b_instance = MagicMock()
    mock_tg_instance = MagicMock()
    mock_uv_instance = MagicMock()

    # Create test args
    class TestArgs:
        install = None
        uninstall = ["1", "2", "3", "4", "5", "6"]

    args = TestArgs()

    # Patch all services to return our mocks
    with (
        patch("app.interfaces.cli.non_interactive.UfwService") as mock_ufw_service,
        patch("app.interfaces.cli.non_interactive.BBRService") as mock_bbr_service,
        patch("app.interfaces.cli.non_interactive.DockerService") as mock_docker_service,
        patch("app.interfaces.cli.non_interactive.Fail2BanService") as mock_f2b_service,
        patch("app.interfaces.cli.non_interactive.TrafficGuardService") as mock_tg_service,
        patch("app.interfaces.cli.non_interactive.UVService") as mock_uv_service,
    ):
        mock_ufw_service.return_value = mock_ufw_instance
        mock_bbr_service.return_value = mock_bbr_instance
        mock_docker_service.return_value = mock_docker_instance
        mock_f2b_service.return_value = mock_f2b_instance
        mock_tg_service.return_value = mock_tg_instance
        mock_uv_service.return_value = mock_uv_instance

        result = run_non_interactive_commands(args)

        assert result is True
        mock_ufw_instance.uninstall.assert_called_once()
        mock_bbr_instance.uninstall.assert_called_once()
        mock_docker_instance.uninstall.assert_called_once()
        mock_f2b_instance.uninstall.assert_called_once()
        mock_tg_instance.uninstall.assert_called_once()
        mock_uv_instance.uninstall.assert_called_once()


def test_run_non_interactive_install_uninstall_same_service():
    """Test non-interactive mode with install and uninstall for the same service"""
    # Create mock instances
    mock_bbr_instance = MagicMock()

    # Create test args to install and uninstall BBR
    class TestArgs:
        install = ["2"]  # Install BBR
        uninstall = ["2"]  # Also uninstall BBR

    args = TestArgs()

    # Patch the service to return our mock
    with patch("app.interfaces.cli.non_interactive.BBRService") as mock_bbr_service:
        mock_bbr_service.return_value = mock_bbr_instance

        result = run_non_interactive_commands(args)

        assert result is True
        mock_bbr_instance.install.assert_called_once()
        mock_bbr_instance.uninstall.assert_called_once()


def test_run_non_interactive_returns_false_when_service_returns_false():
    """Test non-interactive mode propagates explicit service failure."""

    class TestArgs:
        install = ["1"]
        uninstall = None

    args = TestArgs()
    mock_ufw_instance = MagicMock()
    mock_ufw_instance.install.return_value = False

    with patch("app.interfaces.cli.non_interactive.UfwService") as mock_ufw_service:
        mock_ufw_service.return_value = mock_ufw_instance

        result = run_non_interactive_commands(args)

    assert result is False
    mock_ufw_instance.install.assert_called_once()
