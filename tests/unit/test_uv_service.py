from pathlib import Path
from unittest.mock import Mock, patch

from app.i18n.locale import t
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
            mock_run.assert_called_once_with(
                self.service._get_uv_command("--version"), check=False
            )

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

    def test_get_info_lines_returns_service_info(self):
        assert self.service.get_info_lines() == (
            t("info.uv.line1"),
            t("info.uv.line2"),
            t("info.uv.line3"),
            t("info.uv.line4"),
            t("info.uv.line5"),
            t("info.uv.line6"),
            t("info.uv.line7"),
            t("info.uv.line8"),
            t("info.uv.line9"),
            t("info.uv.line10"),
        )

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
    def test_is_path_configured_already_present(self, mock_environ_get, mock_home):
        """Тест проверки PATH когда путь уже добавлен"""
        mock_home.return_value = Path("/root")  # Docker container uses root user
        mock_environ_get.return_value = (
            "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/root/.local/bin"
        )

        assert self.service._is_path_configured() is True

    @patch("app.services.uv.Path.home")
    @patch("os.environ.get")
    def test_is_path_configured_missing(self, mock_environ_get, mock_home):
        """Тест проверки PATH когда путь отсутствует"""
        mock_environ_get.return_value = "/usr/bin:/bin"
        mock_home.return_value = Path("/home/user")

        assert self.service._is_path_configured() is False

    @patch("os.environ.get", return_value="/usr/bin:/bin")
    @patch("app.services.uv.run")
    def test_get_status_uses_direct_uv_path_when_not_in_path(
        self, mock_run, _mock_environ_get, tmp_path
    ):
        """Статус должен работать, даже если uv есть только в ~/.local/bin"""
        executable = tmp_path / "uv"
        executable.touch()
        self.service.UV_EXECUTABLE = executable
        mock_run.return_value = Mock(returncode=0, stdout="uv 0.7.0\n")

        status = self.service.get_status()

        assert "Статус установки: 🟢 установлен" in status
        assert "Версия uv: uv 0.7.0" in status
        assert "PATH настроен: нет" in status
        mock_run.assert_any_call([str(executable), "--version"], check=False)

    def test_get_status_returns_not_installed_when_uv_is_missing(self):
        with patch.object(UVService, "_is_uv_installed", return_value=False):
            status = self.service.get_status()

        assert status == "Статус установки: 🔴 не установлен"

    @patch("os.environ.get", return_value="/usr/bin:/bin")
    @patch("app.services.uv.run")
    def test_install_already_installed_via_direct_path(
        self, mock_run, _mock_environ_get, tmp_path
    ):
        """Установка не должна переустанавливать uv, если бинарник есть вне PATH"""
        executable = tmp_path / "uv"
        executable.touch()
        self.service.UV_EXECUTABLE = executable
        mock_run.return_value = Mock(returncode=0, stdout="uv 0.7.0\n")

        result = self.service.install()

        assert result is True
        version_calls = [
            call_args
            for call_args in mock_run.call_args_list
            if call_args.args == ([str(executable), "--version"],)
        ]
        assert version_calls
        assert not any(
            "uv_install.sh" in " ".join(call.args[0]) for call in mock_run.call_args_list
        )

    @patch("app.services.uv.logger")
    @patch("os.environ.get", return_value="/usr/bin:/bin")
    @patch("app.services.uv.run")
    def test_install_warns_about_missing_path_when_already_installed(
        self, mock_run, _mock_environ_get, mock_logger, tmp_path
    ):
        executable = tmp_path / "uv"
        executable.touch()
        self.service.UV_EXECUTABLE = executable
        mock_run.return_value = Mock(returncode=0, stdout="uv 0.7.0\n")

        result = self.service.install()

        assert result is True
        mock_logger.warning.assert_any_call(
            "⚠️ ~/.local/bin не в PATH. Добавьте в ~/.bashrc или ~/.zshrc:"
        )

    def test_install_already_installed(self, mock_subprocess_result):
        """Тест установки uv когда он уже установлен"""
        version_mock = mock_subprocess_result(returncode=0, stdout="uv 0.2.4")

        with patch("app.services.uv.run") as mock_run, patch("os.environ.get") as mock_environ_get:
            # Mock PATH to not contain the UV path so _add_to_path_if_needed returns False
            mock_environ_get.return_value = (
                "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
            )
            mock_run.return_value = version_mock

            self.service.install()

            # Повторная проверка версии допустима для идемпотентной установки.
            # So we expect 2 calls: one for the initial check and one from _add_to_path_if_needed
            assert mock_run.call_count == 2
            mock_run.assert_any_call(self.service._get_uv_command("--version"), check=False)

    @patch("app.services.uv.run")
    def test_uninstall_not_installed(self, mock_run):
        """Тест удаления uv когда он не установлен"""
        # First call to check if installed returns failure, second call to check after removal also fails
        mock_run.side_effect = [Mock(returncode=1), Mock(returncode=1)]

        self.service.uninstall()

        # Should try to check if uv is installed first
        mock_run.assert_any_call(self.service._get_uv_command("--version"), check=False)

    def test_install_first_time(self, mock_subprocess_result):
        """Тест установки uv при первом запуске"""
        # Setup to simulate uv not being installed initially, then getting installed
        side_effects = [
            mock_subprocess_result(returncode=1),  # uv --version fails (not installed)
            mock_subprocess_result(returncode=0, stdout="Downloaded successfully"),  # curl success
            mock_subprocess_result(returncode=0, stdout="Installation completed"),  # bash success
            mock_subprocess_result(returncode=0, stdout=""),  # rm uv_install.sh
            mock_subprocess_result(
                returncode=0, stdout="uv 0.2.4"
            ),  # uv --version success after install
        ]

        with (
            patch("app.services.uv.run") as mock_run,
            patch("os.environ.get", return_value="/some/path"),
        ):
            mock_run.side_effect = side_effects

            self.service.install()

            # Verify the sequence of calls
            assert mock_run.call_count >= 3  # At least check version, download, install

    def test_install_continues_when_curl_package_install_warns(self, mock_subprocess_result):
        side_effects = [
            mock_subprocess_result(returncode=1, stdout=""),  # uv not installed
            mock_subprocess_result(
                returncode=1, stdout="curl already installed"
            ),  # apt install curl
            mock_subprocess_result(returncode=0, stdout="downloaded"),  # curl download
            mock_subprocess_result(returncode=0, stdout="installed"),  # sh installer
            mock_subprocess_result(returncode=0, stdout=""),  # rm installer
            mock_subprocess_result(returncode=0, stdout="uv 0.8.0"),  # final install check
            mock_subprocess_result(returncode=0, stdout="uv 0.8.0"),  # final version check
        ]

        with (
            patch("app.services.uv.run") as mock_run,
            patch("os.environ.get", return_value="/root/.local/bin:/usr/bin"),
        ):
            mock_run.side_effect = side_effects

            assert self.service.install() is True

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

    def test_install_file_not_found_error(self):
        """Тест установки uv с ошибкой FileNotFoundError"""
        with patch.object(UVService, "_is_uv_installed") as mock_is_installed:
            mock_is_installed.return_value = False

            with patch("app.services.uv.run") as mock_run:
                mock_run.side_effect = FileNotFoundError("Command not found")

                # Capture logger to verify error message
                with patch("app.services.uv.logger") as mock_logger:
                    self.service.install()

                    # Should log error but return None
                    mock_logger.error.assert_called()

    def test_install_permission_error(self):
        """Тест установки uv с ошибкой PermissionError"""
        with patch.object(UVService, "_is_uv_installed") as mock_is_installed:
            mock_is_installed.return_value = False

            with patch("app.services.uv.run") as mock_run:
                mock_run.side_effect = PermissionError("Permission denied")

                # Capture logger to verify error message
                with patch("app.services.uv.logger") as mock_logger:
                    self.service.install()

                    # Should log error but return None
                    mock_logger.error.assert_called()

    def test_install_general_exception(self):
        """Тест установки uv с общей ошибкой"""
        with patch.object(UVService, "_is_uv_installed") as mock_is_installed:
            mock_is_installed.return_value = False

            with patch("app.services.uv.run") as mock_run:
                mock_run.side_effect = Exception("General error")

                # Capture logger to verify error message
                with patch("app.services.uv.logger") as mock_logger:
                    self.service.install()

                    # Should log exception
                    mock_logger.exception.assert_called()

    def test_uninstall_file_not_found_error(self):
        """Тест удаления uv с ошибкой FileNotFoundError при проверке установки"""
        with patch.object(UVService, "_is_uv_installed") as mock_is_installed:
            mock_is_installed.side_effect = FileNotFoundError("Command not found")

            # Capture logger to verify message
            with patch("app.services.uv.logger") as mock_logger:
                self.service.uninstall()

                # Should log info that uv is already removed
                mock_logger.info.assert_called()

    def test_uninstall_permission_error(self):
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

                        with patch("app.services.uv.logger"):
                            # Simulate permission error during actual removal process
                            with patch("os.remove") as mock_remove:
                                mock_remove.side_effect = PermissionError("Permission denied")

                                # Call uninstall method
                                self.service.uninstall()

    def test_uninstall_general_exception(self):
        """Тест удаления uv с общей ошибкой"""
        with patch.object(UVService, "_is_uv_installed") as mock_is_installed:
            mock_is_installed.return_value = True  # uv is installed

            with patch("app.services.uv.run") as mock_run:
                mock_run.side_effect = Exception("General error")

                # Capture logger to verify exception logging
                with patch("app.services.uv.logger") as mock_logger:
                    self.service.uninstall()

                    # Should log exception
                    mock_logger.exception.assert_called()

    def test_uninstall_succeeds_with_env_cleanup_and_missing_paths(self):
        with (
            patch.object(UVService, "_is_uv_installed", side_effect=[True, False]),
            patch.object(UVService, "_get_uv_paths", return_value=None),
            patch.object(UVService, "ENV_FILE") as mock_env_file,
            patch("app.services.uv.run") as mock_run,
        ):
            mock_env_file.exists.return_value = True
            mock_run.side_effect = [
                Mock(returncode=1, stdout="cache cleanup warning"),
                Mock(returncode=0, stdout=""),
                Mock(returncode=0, stdout=""),
            ]

            assert self.service.uninstall() is True

    def test_uninstall_returns_false_on_permission_error_from_run(self):
        with (
            patch.object(UVService, "_is_uv_installed", return_value=True),
            patch("app.services.uv.run", side_effect=PermissionError("Permission denied")),
        ):
            assert self.service.uninstall() is False

    def test_is_uv_installed_general_exception(self):
        """Тест проверки установки uv с общей ошибкой"""
        with patch("app.services.uv.run") as mock_run:
            mock_run.side_effect = Exception("General error")

            result = self.service._is_uv_installed()

            # Should return False when general exception occurs
            assert result is False
