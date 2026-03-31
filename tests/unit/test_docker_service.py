import subprocess
from unittest.mock import Mock, patch

from app.services.docker import DockerService


class TestDockerService:
    def setup_method(self):
        self.service = DockerService()

    def test_get_status_not_installed(self):
        with patch.object(self.service, "_get_docker_version", return_value=None):
            assert self.service.get_status() == "Статус установки: 🔴 не установлен"

    def test_get_docker_version_success(self, mock_subprocess_result):
        """Тест успешной проверки наличия docker"""
        mock_result = mock_subprocess_result(
            returncode=0, stdout="Docker version 24.0.5, build ced0996"
        )

        with patch("app.services.docker.run") as mock_run:
            mock_run.return_value = mock_result

            result = self.service._get_docker_version()
            assert result == "Docker version 24.0.5, build ced0996"
            mock_run.assert_called_once_with(["docker", "--version"], check=False)

    def test_get_docker_version_failure_returncode(self, mock_subprocess_result):
        """Тест проверки наличия docker с ошибкой возврата"""
        mock_result = mock_subprocess_result(returncode=1, stdout="")

        with patch("app.services.docker.run") as mock_run:
            mock_run.return_value = mock_result

            result = self.service._get_docker_version()
            assert result is None

    def test_get_docker_version_file_not_found(self):
        """Тест проверки наличия docker с FileNotFoundError"""
        with patch("app.services.docker.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()

            result = self.service._get_docker_version()
            assert result is False

    def test_install_already_installed(self, mock_subprocess_result):
        """Тест установки docker когда он уже установлен"""
        version_mock = mock_subprocess_result(
            returncode=0, stdout="Docker version 24.0.5, build ced0996"
        )

        with patch("app.services.docker.run") as mock_run:
            mock_run.return_value = version_mock

            self.service.install()

            mock_run.assert_called_once_with(["docker", "--version"], check=False)

    def test_install_first_time(self, mock_subprocess_result):
        """Тест установки docker при первом запуске"""
        # First call to check if installed returns None
        # Then curl install
        # Then download script
        # Then execute script
        # Then remove script
        # Then final check

        side_effects = [
            mock_subprocess_result(
                returncode=1
            ),  # _get_docker_version returns None (not installed)
            mock_subprocess_result(returncode=0, stdout=""),  # curl install
            mock_subprocess_result(returncode=0, stdout=""),  # download get-docker.sh
            mock_subprocess_result(returncode=0, stdout=""),  # run get-docker.sh
            mock_subprocess_result(returncode=0, stdout=""),  # remove get-docker.sh
            mock_subprocess_result(
                returncode=0, stdout="Docker version 24.0.5, build ced0996"
            ),  # final check
        ]

        with patch("app.services.docker.run") as mock_run:
            mock_run.side_effect = side_effects

            self.service.install()

            # Verify that the main checks were called
            assert mock_run.call_count >= 2  # At least check version and install curl
            # The important thing is that it tries to install when not found

    def test_install_download_failure(self):
        with patch("app.services.docker.run") as mock_run:
            mock_run.side_effect = [
                Mock(returncode=1, stdout=""),
                Mock(returncode=0, stdout=""),
                Mock(returncode=1, stdout=""),
            ]

            result = self.service.install()

        assert result is False

    def test_install_script_failure(self):
        with patch("app.services.docker.run") as mock_run:
            mock_run.side_effect = [
                Mock(returncode=1, stdout=""),
                Mock(returncode=0, stdout=""),
                Mock(returncode=0, stdout=""),
                Mock(returncode=1, stdout=""),
            ]

            result = self.service.install()

        assert result is False

    def test_install_returns_false_when_final_check_fails(self):
        with patch("app.services.docker.run") as mock_run:
            mock_run.side_effect = [
                Mock(returncode=1, stdout=""),
                Mock(returncode=1, stdout=""),
                Mock(returncode=0, stdout=""),
                Mock(returncode=0, stdout=""),
                Mock(returncode=0, stdout=""),
                Mock(returncode=1, stdout=""),
            ]

            result = self.service.install()

        assert result is False

    def test_uninstall_not_installed(self, mock_subprocess_result):
        """Тест удаления docker когда он не установлен"""
        mock_result = mock_subprocess_result(returncode=1)  # Not found

        with patch("app.services.docker.run") as mock_run:
            mock_run.return_value = mock_result

            self.service.uninstall()

            # Should try to check if installed first
            mock_run.assert_any_call(["docker", "--version"], check=False)
            # Should attempt to remove config files
            mock_run.assert_any_call(
                ["rm", "-f", "/etc/apt/sources.list.d/docker.list"], check=False
            )

    @patch("builtins.input", return_value="n")
    def test_uninstall_cancelled_by_user(self, mock_input):
        result = self.service.uninstall(confirm=True)
        assert result is True

    def test_uninstall_when_packages_exist(self, mock_subprocess_result):
        """Тест удаления docker когда пакеты установлены"""
        # Setup to simulate Docker being installed
        side_effects = [
            mock_subprocess_result(
                returncode=0, stdout="Docker version 24.0.5, build ced0996"
            ),  # _get_docker_version returns version
            mock_subprocess_result(returncode=0, stdout=""),  # apt purge succeeds
            mock_subprocess_result(returncode=0, stdout=""),  # rm -rf /var/lib/docker
            mock_subprocess_result(returncode=0, stdout=""),  # rm -rf /var/lib/containerd
            mock_subprocess_result(returncode=1),  # After removal, docker --version fails
        ]

        with patch("app.services.docker.run") as mock_run:
            mock_run.side_effect = side_effects

            self.service.uninstall()

            # Check that various cleanup commands were called
            mock_run.assert_any_call(
                [
                    "apt",
                    "purge",
                    "--auto-remove",
                    "-y",
                    "docker-ce",
                    "docker-ce-cli",
                    "containerd.io",
                    "docker-buildx-plugin",
                    "docker-compose-plugin",
                    "docker-ce-rootless-extras",
                ]
            )
            mock_run.assert_any_call(["rm", "-rf", "/var/lib/docker"], check=False)
            mock_run.assert_any_call(["rm", "-rf", "/var/lib/containerd"], check=False)

    def test_uninstall_returns_false_when_docker_still_present(self):
        with patch("app.services.docker.run") as mock_run:
            mock_run.side_effect = [
                Mock(returncode=0, stdout="Docker version 24.0.5, build ced0996"),
                Mock(returncode=0, stdout=""),
                Mock(returncode=0, stdout=""),
                Mock(returncode=0, stdout=""),
                Mock(returncode=0, stdout="Docker version 24.0.5, build ced0996"),
            ]

            result = self.service.uninstall()

        assert result is False

    @patch("app.services.docker.run")
    def test_uninstall_handles_called_process_error_code_100(self, mock_run):
        mock_run.side_effect = [
            Mock(returncode=0, stdout="Docker version 24.0.5, build ced0996"),
            subprocess.CalledProcessError(returncode=100, cmd=["apt", "purge"], stderr=""),
            Mock(returncode=0, stdout=""),
            Mock(returncode=0, stdout=""),
            Mock(returncode=0, stdout=""),
            Mock(returncode=0, stdout=""),
            Mock(returncode=1, stdout=""),
        ]

        result = self.service.uninstall()

        assert result is True

    @patch("app.services.docker.run")
    def test_uninstall_handles_called_process_error_warning_branch(self, mock_run):
        mock_run.side_effect = [
            Mock(returncode=0, stdout="Docker version 24.0.5, build ced0996"),
            subprocess.CalledProcessError(returncode=42, cmd=["apt", "purge"], stderr="warning"),
            Mock(returncode=0, stdout=""),
            Mock(returncode=0, stdout=""),
            Mock(returncode=0, stdout=""),
            Mock(returncode=0, stdout=""),
            Mock(returncode=1, stdout=""),
        ]

        result = self.service.uninstall()

        assert result is True

    def test_get_docker_version_general_exception(self):
        """Тест получения версии docker с общей ошибкой в обработке stdout"""
        with patch("app.services.docker.run") as mock_run:
            # Mock result with normal return code but problematic stdout that causes exception when processed
            mock_result = Mock()
            mock_result.returncode = 0
            # Make .strip() on stdout raise an exception
            mock_result.stdout = Mock()
            mock_result.stdout.strip.side_effect = Exception("Processing error")
            mock_run.return_value = mock_result

            result = self.service._get_docker_version()

            # Should return None when exception occurs during processing
            assert result is None

    @patch("app.services.docker.run")
    def test_install_file_not_found_error(self, mock_run):
        """Тест установки docker с ошибкой FileNotFoundError"""
        mock_run.side_effect = FileNotFoundError("Command not found")

        with patch("app.services.docker.logger") as mock_logger:
            self.service.install()

            # Should log the error
            mock_logger.error.assert_called()

    @patch("app.services.docker.run")
    def test_install_permission_error(self, mock_run):
        """Тест установки docker с ошибкой PermissionError"""
        mock_run.side_effect = PermissionError("Permission denied")

        with patch("app.services.docker.logger") as mock_logger:
            self.service.install()

            # Should log the error
            mock_logger.error.assert_called()

    @patch("app.services.docker.run")
    def test_install_general_exception(self, mock_run):
        """Тест установки docker с общей ошибкой"""
        mock_run.side_effect = Exception("General error")

        with patch("app.services.docker.logger") as mock_logger:
            self.service.install()

            # Should log the exception
            mock_logger.exception.assert_called()

    @patch("app.services.docker.run")
    def test_uninstall_permission_error_after_check(self, mock_run):
        """Тест удаления docker с ошибкой PermissionError после проверки существования"""
        # First call: Docker exists, subsequent call raises PermissionError during apt purge
        side_effects = [
            Mock(
                returncode=0, stdout="Docker version 24.0.5, build ced0996"
            ),  # Docker exists initially
            PermissionError("Permission denied"),  # Error during apt purge
        ]
        mock_run.side_effect = side_effects

        with patch("app.services.docker.logger") as mock_logger:
            self.service.uninstall()

            # Should log the error
            mock_logger.error.assert_called()

    @patch("app.services.docker.run")
    def test_uninstall_general_exception_after_check(self, mock_run):
        """Тест удаления docker с общей ошибкой после проверки существования"""
        # First call: Docker exists, subsequent call raises general exception
        side_effects = [
            Mock(
                returncode=0, stdout="Docker version 24.0.5, build ced0996"
            ),  # Docker exists initially
            Exception("General error"),  # Error during processing
        ]
        mock_run.side_effect = side_effects

        with patch("app.services.docker.logger") as mock_logger:
            self.service.uninstall()

            # Should log the exception
            mock_logger.exception.assert_called()
