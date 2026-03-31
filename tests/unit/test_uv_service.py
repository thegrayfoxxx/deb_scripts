import os
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
        python_mock = mock_subprocess_result(
            returncode=0, stdout="/home/user/.cache/uv/python"
        )
        tool_mock = mock_subprocess_result(
            returncode=0, stdout="/home/user/.local/share/uv/tool"
        )

        with patch("app.services.uv.run") as mock_run:
            mock_run.side_effect = [python_mock, tool_mock]

            expected = {
                "python": "/home/user/.cache/uv/python",
                "tool": "/home/user/.local/share/uv/tool",
            }
            assert self.service._get_uv_paths() == expected

    def test_get_uv_paths_failure(self, mock_subprocess_result):
        """Тест получения путей uv с ошибкой"""
        python_mock = mock_subprocess_result(
            returncode=0, stdout="/home/user/.cache/uv/python"
        )
        tool_mock = mock_subprocess_result(returncode=1, stdout="")

        with patch("app.services.uv.run") as mock_run:
            mock_run.side_effect = [python_mock, tool_mock]

            assert self.service._get_uv_paths() is None

    def test_source_uv_env_updates_process_path(self, tmp_path):
        env_file = tmp_path / "env"
        env_file.touch()

        with (
            patch.object(UVService, "ENV_FILE", env_file),
            patch(
                "app.services.uv.run",
                return_value=Mock(returncode=0, stdout="/tmp/bin:/usr/bin"),
            ),
            patch.dict(os.environ, {"PATH": "/usr/bin"}, clear=False),
        ):
            assert self.service._source_uv_env() is True
            assert os.environ["PATH"] == "/tmp/bin:/usr/bin"

    def test_ensure_global_uv_symlinks_creates_links(self, tmp_path):
        local_bin = tmp_path / ".local" / "bin"
        global_bin = tmp_path / "usr" / "local" / "bin"
        local_bin.mkdir(parents=True)
        global_bin.mkdir(parents=True)

        self.service.UV_EXECUTABLE = local_bin / "uv"
        self.service.UVX_EXECUTABLE = local_bin / "uvx"
        self.service.UVW_EXECUTABLE = local_bin / "uvw"
        self.service.GLOBAL_UV_EXECUTABLE = global_bin / "uv"
        self.service.GLOBAL_UVX_EXECUTABLE = global_bin / "uvx"
        self.service.GLOBAL_UVW_EXECUTABLE = global_bin / "uvw"

        for path in (
            self.service.UV_EXECUTABLE,
            self.service.UVX_EXECUTABLE,
            self.service.UVW_EXECUTABLE,
        ):
            path.touch()

        assert self.service._ensure_global_uv_symlinks() is True
        assert self.service.GLOBAL_UV_EXECUTABLE.is_symlink()
        assert self.service.GLOBAL_UV_EXECUTABLE.resolve() == self.service.UV_EXECUTABLE
        assert self.service.GLOBAL_UVX_EXECUTABLE.is_symlink()
        assert self.service.GLOBAL_UVW_EXECUTABLE.is_symlink()

    def test_remove_owned_global_uv_symlinks_keeps_foreign_symlink(self, tmp_path):
        local_bin = tmp_path / ".local" / "bin"
        global_bin = tmp_path / "usr" / "local" / "bin"
        local_bin.mkdir(parents=True)
        global_bin.mkdir(parents=True)

        self.service.UV_EXECUTABLE = local_bin / "uv"
        self.service.UVX_EXECUTABLE = local_bin / "uvx"
        self.service.UVW_EXECUTABLE = local_bin / "uvw"
        self.service.GLOBAL_UV_EXECUTABLE = global_bin / "uv"
        self.service.GLOBAL_UVX_EXECUTABLE = global_bin / "uvx"
        self.service.GLOBAL_UVW_EXECUTABLE = global_bin / "uvw"

        self.service.UV_EXECUTABLE.touch()
        self.service.UVX_EXECUTABLE.touch()
        self.service.UVW_EXECUTABLE.touch()
        self.service.GLOBAL_UV_EXECUTABLE.symlink_to(self.service.UV_EXECUTABLE)
        foreign_target = tmp_path / "foreign-uvx"
        foreign_target.touch()
        self.service.GLOBAL_UVX_EXECUTABLE.symlink_to(foreign_target)

        assert self.service._remove_owned_global_uv_symlinks() is False
        assert not self.service.GLOBAL_UV_EXECUTABLE.exists()
        assert self.service.GLOBAL_UVX_EXECUTABLE.exists()

    @patch("os.environ.get")
    def test_is_path_configured_already_present(self, mock_environ_get):
        """Тест проверки PATH когда путь уже добавлен"""
        mock_environ_get.return_value = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/root/.local/bin"

        with patch.object(
            UVService, "_get_expected_uv_bin_dir", return_value=Path("/root/.local/bin")
        ):
            assert self.service._is_path_configured() is True

    @patch("os.environ.get")
    def test_is_path_configured_uses_resolved_uv_directory(
        self, mock_environ_get, tmp_path
    ):
        executable = tmp_path / "bin" / "uv"
        executable.parent.mkdir()
        executable.touch()
        self.service.UV_EXECUTABLE = executable
        mock_environ_get.return_value = f"/usr/bin:{executable.parent}:/bin"

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

    @patch("os.environ.get")
    @patch("app.services.uv.run")
    def test_get_status_reports_path_configured_for_resolved_uv_directory(
        self, mock_run, mock_environ_get, tmp_path
    ):
        executable = tmp_path / "bin" / "uv"
        executable.parent.mkdir()
        executable.touch()
        self.service.UV_EXECUTABLE = executable
        mock_environ_get.return_value = f"/usr/bin:{executable.parent}:/bin"
        mock_run.return_value = Mock(returncode=0, stdout="uv 0.11.2\n")

        status = self.service.get_status()

        assert "Статус установки: 🟢 установлен" in status
        assert "Версия uv: uv 0.11.2" in status
        assert "PATH настроен: да" in status

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

        with (
            patch.object(UVService, "_source_uv_env", return_value=False),
            patch.object(UVService, "_ensure_global_uv_symlinks", return_value=True),
        ):
            result = self.service.install()

        assert result is True
        version_calls = [
            call_args
            for call_args in mock_run.call_args_list
            if call_args.args == ([str(executable), "--version"],)
        ]
        assert version_calls
        assert not any(
            "uv_install.sh" in " ".join(call.args[0])
            for call in mock_run.call_args_list
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

        with (
            patch.object(UVService, "_source_uv_env", return_value=False),
            patch.object(UVService, "_ensure_global_uv_symlinks", return_value=True),
        ):
            result = self.service.install()

        assert result is True
        mock_logger.warning.assert_any_call(
            f"⚠️ {tmp_path} не в PATH. Добавьте в ~/.bashrc или ~/.zshrc:"
        )

    def test_install_already_installed(self, mock_subprocess_result):
        """Тест установки uv когда он уже установлен"""
        version_mock = mock_subprocess_result(returncode=0, stdout="uv 0.2.4")

        with (
            patch("app.services.uv.run") as mock_run,
            patch("os.environ.get") as mock_environ_get,
            patch.object(UVService, "_source_uv_env", return_value=False),
            patch.object(UVService, "_ensure_global_uv_symlinks", return_value=True),
        ):
            # Mock PATH to not contain the UV path so _add_to_path_if_needed returns False
            mock_environ_get.return_value = (
                "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
            )
            mock_run.return_value = version_mock

            self.service.install()

            # Повторная проверка версии допустима для идемпотентной установки.
            # So we expect 2 calls: one for the initial check and one from _add_to_path_if_needed
            assert mock_run.call_count == 2
            mock_run.assert_any_call(
                self.service._get_uv_command("--version"), check=False
            )

    @patch("app.services.uv.run")
    def test_uninstall_not_installed(self, mock_run):
        """Тест удаления uv когда он не установлен"""
        binary_targets = (
            Path("/root/.local/bin/uv"),
            Path("/root/.local/bin/uvx"),
            Path("/root/.local/bin/uvw"),
        )
        mock_run.side_effect = [
            Mock(returncode=1, stdout=""),
            Mock(returncode=0, stdout=""),
        ]

        with patch.object(
            UVService, "_get_uv_binary_targets", return_value=binary_targets
        ):
            assert self.service.uninstall() is True

        mock_run.assert_any_call(self.service._get_uv_command("--version"), check=False)
        mock_run.assert_any_call(
            ["rm", "-f", *(str(path) for path in binary_targets)],
            check=False,
        )

    def test_install_first_time(self, mock_subprocess_result):
        """Тест установки uv при первом запуске"""
        side_effects = [
            mock_subprocess_result(returncode=1),  # uv --version fails (not installed)
            mock_subprocess_result(returncode=0, stdout="curl installed"),  # apt curl
            mock_subprocess_result(
                returncode=0, stdout="Installation completed"
            ),  # install
            mock_subprocess_result(
                returncode=0, stdout="uv 0.2.4"
            ),  # uv --version success after install
            mock_subprocess_result(
                returncode=0, stdout="uv 0.2.4"
            ),  # final version check
        ]

        with (
            patch("app.services.uv.run") as mock_run,
            patch("os.environ.get", return_value="/some/path"),
            patch.object(UVService, "_source_uv_env", return_value=True),
            patch.object(UVService, "_ensure_global_uv_symlinks", return_value=True),
        ):
            mock_run.side_effect = side_effects

            assert self.service.install() is True
            mock_run.assert_any_call(
                ["bash", "-lc", f"curl -LsSf {self.service.UV_INSTALL_URL} | sh"],
                check=False,
                env=self.service._get_shell_env(),
            )

    def test_install_continues_when_curl_package_install_warns(
        self, mock_subprocess_result
    ):
        side_effects = [
            mock_subprocess_result(returncode=1, stdout=""),  # uv not installed
            mock_subprocess_result(
                returncode=1, stdout="curl already installed"
            ),  # apt install curl
            mock_subprocess_result(returncode=0, stdout="installed"),  # sh installer
            mock_subprocess_result(
                returncode=0, stdout="uv 0.8.0"
            ),  # final install check
            mock_subprocess_result(
                returncode=0, stdout="uv 0.8.0"
            ),  # final version check
        ]

        with (
            patch("app.services.uv.run") as mock_run,
            patch("os.environ.get", return_value="/root/.local/bin:/usr/bin"),
            patch.object(UVService, "_source_uv_env", return_value=True),
            patch.object(UVService, "_ensure_global_uv_symlinks", return_value=True),
        ):
            mock_run.side_effect = side_effects

            assert self.service.install() is True

    def test_install_returns_false_when_global_symlink_publish_fails(
        self, mock_subprocess_result
    ):
        side_effects = [
            mock_subprocess_result(returncode=1, stdout=""),
            mock_subprocess_result(returncode=0, stdout="curl installed"),
            mock_subprocess_result(returncode=0, stdout="Installation completed"),
        ]

        with (
            patch("app.services.uv.run") as mock_run,
            patch.object(UVService, "_source_uv_env", return_value=True),
            patch.object(UVService, "_ensure_global_uv_symlinks", return_value=False),
        ):
            mock_run.side_effect = side_effects

            assert self.service.install() is False

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

    def test_uninstall_returns_false_when_uv_still_in_path(self, tmp_path):
        binary_targets = (
            tmp_path / "uv",
            tmp_path / "uvx",
            tmp_path / "uvw",
        )
        for path in binary_targets:
            path.touch()

        def run_side_effect(command, check=False):
            if command[:2] == [str(binary_targets[0]), "cache"]:
                return Mock(returncode=0, stdout="cache cleaned")
            if command[:2] == ["rm", "-f"]:
                for raw_path in command[2:]:
                    Path(raw_path).unlink(missing_ok=True)
                return Mock(returncode=0, stdout="")
            raise AssertionError(f"Unexpected command: {command}")

        with (
            patch.object(UVService, "_is_uv_installed", return_value=True),
            patch.object(UVService, "_get_uv_paths", return_value=None),
            patch.object(
                UVService, "_get_uv_binary_targets", return_value=binary_targets
            ),
            patch.object(UVService, "ENV_FILE", tmp_path / "env"),
            patch("app.services.uv.run", side_effect=run_side_effect),
            patch("app.services.uv.shutil.which", return_value="/usr/bin/uv"),
        ):
            assert self.service.uninstall() is False

    def test_uninstall_removes_all_uv_binaries_found_in_path(self, tmp_path):
        local_bin = tmp_path / ".local" / "bin"
        local_bin.mkdir(parents=True)
        usr_local_bin = tmp_path / "usr" / "local" / "bin"
        usr_local_bin.mkdir(parents=True)

        path_binaries = (
            local_bin / "uv",
            local_bin / "uvx",
            local_bin / "uvw",
            usr_local_bin / "uv",
            usr_local_bin / "uvx",
            usr_local_bin / "uvw",
        )
        for path in path_binaries:
            path.touch()

        self.service.UV_EXECUTABLE = local_bin / "uv"
        self.service.UVX_EXECUTABLE = local_bin / "uvx"
        self.service.UVW_EXECUTABLE = local_bin / "uvw"
        env_file = local_bin / "env"
        env_file.touch()

        def run_side_effect(command, check=False):
            if command[:2] == [str(local_bin / "uv"), "cache"]:
                return Mock(returncode=0, stdout="cache cleaned")
            if command[:2] == ["rm", "-f"]:
                for raw_path in command[2:]:
                    Path(raw_path).unlink(missing_ok=True)
                return Mock(returncode=0, stdout="")
            raise AssertionError(f"Unexpected command: {command}")

        with (
            patch.object(UVService, "_is_uv_installed", return_value=True),
            patch.object(UVService, "_get_uv_paths", return_value=None),
            patch.object(UVService, "ENV_FILE", env_file),
            patch.dict(
                os.environ,
                {"PATH": f"{local_bin}:{usr_local_bin}:/usr/bin"},
                clear=False,
            ),
            patch("app.services.uv.run", side_effect=run_side_effect) as mock_run,
            patch(
                "app.services.uv.shutil.which",
                side_effect=lambda _: (
                    str(local_bin / "uv") if (local_bin / "uv").exists() else None
                ),
            ),
        ):
            assert self.service.uninstall() is True

        mock_run.assert_any_call(
            [
                "rm",
                "-f",
                *(str(path) for path in sorted(path_binaries, key=lambda p: str(p))),
            ],
            check=False,
        )

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

    def test_uninstall_succeeds_with_env_cleanup_and_missing_paths(self, tmp_path):
        binary_targets = (
            tmp_path / "uv",
            tmp_path / "uvx",
            tmp_path / "uvw",
        )
        for path in binary_targets:
            path.touch()

        env_file = tmp_path / "env"
        env_file.touch()
        self.service.UV_EXECUTABLE = binary_targets[0]

        def run_side_effect(command, check=False):
            if command[:2] == [str(binary_targets[0]), "cache"]:
                return Mock(returncode=1, stdout="cache cleanup warning")
            if command[:2] == ["rm", "-f"]:
                for raw_path in command[2:]:
                    Path(raw_path).unlink(missing_ok=True)
                return Mock(returncode=0, stdout="")
            raise AssertionError(f"Unexpected command: {command}")

        with (
            patch.object(UVService, "_is_uv_installed", return_value=True),
            patch.object(UVService, "_get_uv_paths", return_value=None),
            patch.object(
                UVService, "_get_uv_binary_targets", return_value=binary_targets
            ),
            patch.object(UVService, "_get_uv_binaries_from_path", return_value=()),
            patch.object(UVService, "ENV_FILE", env_file),
            patch("app.services.uv.run", side_effect=run_side_effect) as mock_run,
            patch(
                "app.services.uv.shutil.which",
                side_effect=lambda _: (
                    str(binary_targets[0]) if binary_targets[0].exists() else None
                ),
            ),
        ):
            assert self.service.uninstall() is True

        mock_run.assert_any_call(
            ["rm", "-f", *(str(path) for path in binary_targets)],
            check=False,
        )
        mock_run.assert_any_call(["rm", "-f", str(env_file)], check=False)

    def test_uninstall_succeeds_with_custom_install_dir_and_removes_uvw(self, tmp_path):
        custom_bin_dir = tmp_path / "bin"
        custom_bin_dir.mkdir()
        env_file = custom_bin_dir / "env"
        env_file.touch()

        binary_targets = (
            custom_bin_dir / "uv",
            custom_bin_dir / "uvx",
            custom_bin_dir / "uvw",
        )
        for path in binary_targets:
            path.touch()
        self.service.UV_EXECUTABLE = tmp_path / ".local" / "bin" / "uv"

        def run_side_effect(command, check=False):
            if command[:2] == [str(binary_targets[0]), "cache"]:
                return Mock(returncode=0, stdout="cache cleaned")
            if command[:2] == ["rm", "-f"]:
                for raw_path in command[2:]:
                    Path(raw_path).unlink(missing_ok=True)
                return Mock(returncode=0, stdout="")
            raise AssertionError(f"Unexpected command: {command}")

        with (
            patch.object(UVService, "_is_uv_installed", return_value=True),
            patch.object(UVService, "_get_uv_paths", return_value=None),
            patch.object(
                UVService, "_get_uv_binary_targets", return_value=binary_targets
            ),
            patch.object(UVService, "_get_uv_binaries_from_path", return_value=()),
            patch.object(UVService, "ENV_FILE", env_file),
            patch("app.services.uv.run", side_effect=run_side_effect) as mock_run,
            patch(
                "app.services.uv.shutil.which",
                side_effect=lambda _: (
                    str(binary_targets[0]) if binary_targets[0].exists() else None
                ),
            ),
        ):
            assert self.service.uninstall() is True

        mock_run.assert_any_call(
            ["rm", "-f", *(str(path) for path in binary_targets)],
            check=False,
        )

    def test_uninstall_returns_false_on_permission_error_from_run(self):
        with (
            patch.object(UVService, "_is_uv_installed", return_value=True),
            patch(
                "app.services.uv.run", side_effect=PermissionError("Permission denied")
            ),
        ):
            assert self.service.uninstall() is False

    def test_is_uv_installed_general_exception(self):
        """Тест проверки установки uv с общей ошибкой"""
        with patch("app.services.uv.run") as mock_run:
            mock_run.side_effect = Exception("General error")

            result = self.service._is_uv_installed()

            # Should return False when general exception occurs
            assert result is False
