from unittest.mock import patch

from app.services.docker import DockerService


class TestDockerService:
    def setup_method(self):
        self.service = DockerService()

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

    def test_install_docker_already_installed(self, mock_subprocess_result):
        """Тест установки docker когда он уже установлен"""
        version_mock = mock_subprocess_result(
            returncode=0, stdout="Docker version 24.0.5, build ced0996"
        )

        with (
            patch("app.services.docker.update_os") as mock_update_os,
            patch("app.services.docker.run") as mock_run,
        ):
            mock_run.return_value = version_mock

            self.service.install_docker()

            mock_run.assert_called_once_with(["docker", "--version"], check=False)
            mock_update_os.assert_not_called()

    def test_install_docker_first_time(self, mock_subprocess_result):
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

        with (
            patch("app.services.docker.update_os") as mock_update_os,
            patch("app.services.docker.run") as mock_run,
        ):
            mock_run.side_effect = side_effects

            self.service.install_docker()

            # Verify that the main checks were called
            assert mock_run.call_count >= 2  # At least check version and install curl
            # The important thing is that it tries to install when not found

    def test_uninstall_docker_not_installed(self, mock_subprocess_result):
        """Тест удаления docker когда он не установлен"""
        mock_result = mock_subprocess_result(returncode=1)  # Not found

        with patch("app.services.docker.run") as mock_run:
            mock_run.return_value = mock_result

            self.service.uninstall_docker()

            # Should try to check if installed first
            mock_run.assert_any_call(["docker", "--version"], check=False)
            # Should attempt to remove config files
            mock_run.assert_any_call(
                ["rm", "-f", "/etc/apt/sources.list.d/docker.list"], check=False
            )

    def test_uninstall_docker_when_packages_exist(self, mock_subprocess_result):
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

            self.service.uninstall_docker()

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
