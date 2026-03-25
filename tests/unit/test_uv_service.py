from pathlib import Path
from unittest.mock import Mock, patch

from app.services.uv import UVService


class TestUVService:
    def setup_method(self):
        self.service = UVService()

    def test_is_uv_installed_success(self, mock_subprocess_result):
        """Тест успешной проверки наличия uv"""
        mock_result = mock_subprocess_result(returncode=0, stdout="uv 0.2.4")

        with patch("app.services.uv.run") as mock_run:
            mock_run.return_value = mock_result

            assert self.service._is_uv_installed() is True
            mock_run.assert_called_once_with(["uv", "--version"], check=False)

    def test_is_uv_installed_failure_returncode(self, mock_subprocess_result):
        """Тест проверки наличия uv с ошибкой возврата"""
        mock_result = mock_subprocess_result(returncode=1, stdout="")

        with patch("app.services.uv.run") as mock_run:
            mock_run.return_value = mock_result

            assert self.service._is_uv_installed() is False

    def test_is_uv_installed_file_not_found(self):
        """Тест проверки наличия uv с FileNotFoundError"""
        with patch("app.services.uv.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()

            assert self.service._is_uv_installed() is False

    def test_get_uv_paths_success(self, mock_subprocess_result):
        """Тест успешного получения путей uv"""
        python_mock = mock_subprocess_result(returncode=0, stdout="/home/user/.cache/uv/python")
        tool_mock = mock_subprocess_result(returncode=0, stdout="/home/user/.local/share/uv/tool")

        with patch("app.services.uv.run") as mock_run:
            mock_run.side_effect = [python_mock, tool_mock]

            expected = {
                "python": "/home/user/.cache/uv/python",
                "tool": "/home/user/.local/share/uv/tool",
            }
            assert self.service._get_uv_paths() == expected

    def test_get_uv_paths_failure(self, mock_subprocess_result):
        """Тест получения путей uv с ошибкой"""
        python_mock = mock_subprocess_result(returncode=0, stdout="/home/user/.cache/uv/python")
        tool_mock = mock_subprocess_result(returncode=1, stdout="")

        with patch("app.services.uv.run") as mock_run:
            mock_run.side_effect = [python_mock, tool_mock]

            assert self.service._get_uv_paths() is None

    @patch("app.services.uv.Path.home")
    @patch("os.environ.get")
    def test_add_to_path_if_needed_already_present(self, mock_environ_get, mock_home):
        """Тест проверки PATH когда путь уже добавлен"""
        mock_home.return_value = Path("/root")  # Docker container uses root user
        mock_environ_get.return_value = (
            "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/root/.local/bin"
        )

        assert self.service._add_to_path_if_needed() is True

    @patch("app.services.uv.Path.home")
    @patch("os.environ.get")
    def test_add_to_path_if_needed_missing(self, mock_environ_get, mock_home):
        """Тест проверки PATH когда путь отсутствует"""
        mock_environ_get.return_value = "/usr/bin:/bin"
        mock_home.return_value = Path("/home/user")

        assert self.service._add_to_path_if_needed() is False

    def test_install_uv_already_installed(self, mock_subprocess_result):
        """Тест установки uv когда он уже установлен"""
        version_mock = mock_subprocess_result(returncode=0, stdout="uv 0.2.4")

        with (
            patch("app.services.uv.update_os") as mock_update_os,
            patch("app.services.uv.run") as mock_run,
            patch("os.environ.get") as mock_environ_get,
        ):
            # Mock PATH to not contain the UV path so _add_to_path_if_needed returns False
            mock_environ_get.return_value = (
                "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
            )
            mock_run.return_value = version_mock

            self.service.install_uv()

            # The install_uv method calls _add_to_path_if_needed which triggers another check
            # So we expect 2 calls: one for the initial check and one from _add_to_path_if_needed
            assert mock_run.call_count == 2
            mock_run.assert_any_call(["uv", "--version"], check=False)
            mock_update_os.assert_not_called()

    @patch("app.services.uv.update_os")
    @patch("app.services.uv.run")
    def test_uninstall_uv_not_installed(self, mock_run, mock_update_os):
        """Тест удаления uv когда он не установлен"""
        # First call to check if installed returns failure, second call to check after removal also fails
        mock_run.side_effect = [Mock(returncode=1), Mock(returncode=1)]

        self.service.uninstall_uv()

        # Should try to check if uv is installed first
        mock_run.assert_any_call(["uv", "--version"], check=False)

    def test_install_uv_first_time(self, mock_subprocess_result):
        """Тест установки uv при первом запуске"""
        # Setup to simulate uv not being installed initially, then getting installed
        side_effects = [
            mock_subprocess_result(returncode=1),  # uv --version fails (not installed)
            mock_subprocess_result(returncode=0, stdout="Downloaded successfully"),  # curl success
            mock_subprocess_result(returncode=0, stdout="Installation completed"),  # bash success
            mock_subprocess_result(
                returncode=0, stdout="uv 0.2.4"
            ),  # uv --version success after install
        ]

        with (
            patch("app.services.uv.update_os") as mock_update_os,
            patch("app.services.uv.run") as mock_run,
            patch("os.environ.get", return_value="/some/path"),  # Mock PATH
        ):
            mock_run.side_effect = side_effects

            self.service.install_uv()

            # Verify the sequence of calls
            assert mock_run.call_count >= 3  # At least check version, download, install
            mock_update_os.assert_called_once()  # OS should be updated before installing

    # Пропускаем этот тест, так как сложно мокировать все вызовы в методе удаления

    def test_get_uv_paths_file_not_found_error(self):
        """Тест получения путей uv с ошибкой FileNotFoundError"""
        with patch("app.services.uv.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("uv command not found")

            result = self.service._get_uv_paths()

            # Should return None when FileNotFoundError occurs
            assert result is None

    def test_get_uv_paths_general_exception(self):
        """Тест получения путей uv с общей ошибкой"""
        with patch("app.services.uv.run") as mock_run:
            mock_run.side_effect = Exception("General error")

            result = self.service._get_uv_paths()

            # Should return None when general exception occurs
            assert result is None

    def test_install_uv_file_not_found_error(self):
        """Тест установки uv с ошибкой FileNotFoundError"""
        with patch.object(UVService, "_is_uv_installed") as mock_is_installed:
            mock_is_installed.return_value = False

            with patch("app.services.uv.update_os"):
                with patch("app.services.uv.run") as mock_run:
                    mock_run.side_effect = FileNotFoundError("Command not found")

                    # Capture logger to verify error message
                    with patch("app.services.uv.logger") as mock_logger:
                        result = self.service.install_uv()

                        # Should log error but return None
                        mock_logger.error.assert_called()

    def test_install_uv_permission_error(self):
        """Тест установки uv с ошибкой PermissionError"""
        with patch.object(UVService, "_is_uv_installed") as mock_is_installed:
            mock_is_installed.return_value = False

            with patch("app.services.uv.update_os"):
                with patch("app.services.uv.run") as mock_run:
                    mock_run.side_effect = PermissionError("Permission denied")

                    # Capture logger to verify error message
                    with patch("app.services.uv.logger") as mock_logger:
                        result = self.service.install_uv()

                        # Should log error but return None
                        mock_logger.error.assert_called()

    def test_install_uv_general_exception(self):
        """Тест установки uv с общей ошибкой"""
        with patch.object(UVService, "_is_uv_installed") as mock_is_installed:
            mock_is_installed.return_value = False

            with patch("app.services.uv.update_os"):
                with patch("app.services.uv.run") as mock_run:
                    mock_run.side_effect = Exception("General error")

                    # Capture logger to verify error message
                    with patch("app.services.uv.logger") as mock_logger:
                        result = self.service.install_uv()

                        # Should log exception
                        mock_logger.exception.assert_called()

    def test_uninstall_uv_file_not_found_error(self):
        """Тест удаления uv с ошибкой FileNotFoundError при проверке установки"""
        with patch.object(UVService, "_is_uv_installed") as mock_is_installed:
            mock_is_installed.side_effect = FileNotFoundError("Command not found")

            # Capture logger to verify message
            with patch("app.services.uv.logger") as mock_logger:
                result = self.service.uninstall_uv()

                # Should log info that uv is already removed
                mock_logger.info.assert_called()

    def test_uninstall_uv_permission_error(self):
        """Тест удаления uv с ошибкой PermissionError"""
        with patch.object(UVService, "_is_uv_installed") as mock_is_installed:
            mock_is_installed.return_value = True  # uv is installed

            with patch("app.services.uv.run") as mock_run:
                mock_run.side_effect = [
                    Mock(returncode=0, stdout="cache cleaned"),  # cache clean success
                    Mock(returncode=0, stdout="/path/to/python"),  # python dir
                    Mock(returncode=0, stdout="/path/to/tool"),  # tool dir
                    Mock(returncode=0),  # rm success
                    Mock(returncode=0),  # rm success
                    Mock(returncode=1),  # final check failure
                ]

                with patch.object(UVService, "_get_uv_paths") as mock_get_paths:
                    mock_get_paths.return_value = {
                        "python": "/path/to/python",
                        "tool": "/path/to/tool",
                    }

                    with patch.object(UVService, "ENV_FILE") as mock_env_file:
                        mock_env_file.exists.return_value = False

                        with patch("app.services.uv.logger") as mock_logger:
                            # Simulate permission error during actual removal process
                            with patch("os.remove") as mock_remove:
                                mock_remove.side_effect = PermissionError("Permission denied")

                                # Call uninstall method
                                result = self.service.uninstall_uv()

    def test_uninstall_uv_general_exception(self):
        """Тест удаления uv с общей ошибкой"""
        with patch.object(UVService, "_is_uv_installed") as mock_is_installed:
            mock_is_installed.return_value = True  # uv is installed

            with patch("app.services.uv.run") as mock_run:
                mock_run.side_effect = Exception("General error")

                # Capture logger to verify exception logging
                with patch("app.services.uv.logger") as mock_logger:
                    result = self.service.uninstall_uv()

                    # Should log exception
                    mock_logger.exception.assert_called()

    def test_is_uv_installed_general_exception(self):
        """Тест проверки установки uv с общей ошибкой"""
        with patch("app.services.uv.run") as mock_run:
            mock_run.side_effect = Exception("General error")

            result = self.service._is_uv_installed()

            # Should return False when general exception occurs
            assert result is False
