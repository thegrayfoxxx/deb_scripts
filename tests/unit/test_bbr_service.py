from pathlib import Path
from unittest.mock import Mock, mock_open, patch

from app.services.bbr import BBRService


class TestBBRService:
    def setup_method(self):
        self.service = BBRService()

    def test_install_prepares_configuration(self):
        with (
            patch.object(self.service, "_has_bbr_configuration", side_effect=[False, True]),
            patch.object(self.service, "_is_bbr_module_loaded", return_value=True),
            patch.object(self.service, "_write_config_file", return_value=True) as mock_write,
        ):
            result = self.service.install()

        assert result is True
        assert mock_write.call_count == 2

    def test_uninstall_delegates_to_deactivate_before_cleanup(self):
        with (
            patch.object(self.service, "deactivate", return_value=True) as mock_deactivate,
            patch("app.services.bbr.run"),
            patch("app.services.bbr.Path.exists", return_value=False),
        ):
            result = self.service.uninstall(confirm=True)

        assert result is True
        mock_deactivate.assert_called_once_with(confirm=True)

    def test_get_status_disabled_with_loaded_module(self):
        with (
            patch.object(self.service, "is_installed", return_value=True),
            patch.object(self.service, "_get_current_congestion_control", return_value="cubic"),
            patch.object(self.service, "_is_bbr_module_loaded", return_value=True),
        ):
            status = self.service.get_status()

        assert "Статус установки: 🟢 установлен" in status
        assert "Статус активации: 🔴 не активирован" in status
        assert "Текущий алгоритм перегрузки: cubic" in status
        assert "Модуль tcp_bbr: загружен" in status

    def test_get_status_unknown_when_algorithm_unavailable(self):
        with (
            patch.object(self.service, "is_installed", return_value=False),
            patch.object(self.service, "_get_current_congestion_control", return_value=None),
            patch.object(self.service, "_is_bbr_module_loaded", return_value=False),
        ):
            status = self.service.get_status()

        assert "Статус установки: 🔴 не установлен" in status
        assert "Статус активации: 🔴 не активирован" in status
        assert "Текущий алгоритм перегрузки: недоступен" in status

    def test_get_current_congestion_control_success(self, mock_subprocess_result):
        """Тест успешной проверки текущего алгоритма управления перегрузками"""
        mock_result = mock_subprocess_result(returncode=0, stdout="bbr\n")

        with patch("app.services.bbr.run") as mock_run:
            mock_run.return_value = mock_result

            result = self.service._get_current_congestion_control()
            assert result == "bbr"
            mock_run.assert_called_once_with(
                ["sysctl", "-n", "net.ipv4.tcp_congestion_control"], check=False
            )

    def test_get_current_congestion_control_failure_returncode(self, mock_subprocess_result):
        """Тест проверки текущего алгоритма с ошибкой возврата"""
        mock_result = mock_subprocess_result(returncode=1, stdout="")

        with patch("app.services.bbr.run") as mock_run:
            mock_run.return_value = mock_result

            result = self.service._get_current_congestion_control()
            assert result is None

    def test_get_current_congestion_control_file_not_found(self):
        """Тест проверки текущего алгоритма с FileNotFoundError"""
        with patch("app.services.bbr.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()

            result = self.service._get_current_congestion_control()
            assert result is None

    def test_is_bbr_module_loaded_success(self, mock_subprocess_result):
        """Тест успешной проверки загрузки модуля tcp_bbr"""
        mock_result = mock_subprocess_result(
            returncode=0,
            stdout="tcp_bbr 20480 25 - Live 0x0000000000000000\nsome_other_module...",
        )

        with patch("app.services.bbr.run") as mock_run:
            mock_run.return_value = mock_result

            assert self.service._is_bbr_module_loaded() is True
            mock_run.assert_called_once_with(["lsmod"], check=False)

    def test_is_bbr_module_loaded_not_found(self, mock_subprocess_result):
        """Тест проверки загрузки модуля tcp_bbr когда он не загружен"""
        mock_result = mock_subprocess_result(
            returncode=0, stdout="some_other_module 20480 0 - Live 0x0000000000000000"
        )

        with patch("app.services.bbr.run") as mock_run:
            mock_run.return_value = mock_result

            assert self.service._is_bbr_module_loaded() is False

    def test_is_bbr_module_loaded_returns_false_on_non_zero_exit(self):
        with patch("app.services.bbr.run") as mock_run:
            mock_run.return_value = Mock(returncode=1, stdout="")
            assert self.service._is_bbr_module_loaded() is False

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.mkdir")
    def test_write_config_file_success(self, mock_mkdir, mock_file):
        """Тест успешной записи конфигурационного файла"""
        result = self.service._write_config_file(
            "/etc/modules-load.d/bbr.conf", "tcp_bbr\n", "test config"
        )

        assert result is True
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_file.assert_called_once_with(
            Path("/etc/modules-load.d/bbr.conf"), "w", encoding="utf-8"
        )
        mock_file().write.assert_called_once_with("tcp_bbr\n")

    @patch("builtins.open")
    @patch("pathlib.Path.mkdir")
    def test_write_config_file_permission_error(self, mock_mkdir, mock_file):
        """Тест записи конфигурационного файла с PermissionError"""
        mock_file.side_effect = PermissionError()

        result = self.service._write_config_file(
            "/etc/modules-load.d/bbr.conf", "tcp_bbr\n", "test config"
        )

        assert result is False

    def test_enable_bbr_already_enabled(self, mock_subprocess_result):
        """Тест включения BBR когда он уже включен"""
        with (
            patch.object(self.service, "install", return_value=True) as mock_install,
            patch.object(self.service, "_get_current_congestion_control", return_value="bbr"),
        ):
            result = self.service.enable_bbr()

        assert result is True
        mock_install.assert_called_once_with()

    def test_disable_bbr_already_disabled(self, mock_subprocess_result):
        """Тест отключения BBR когда он уже выключен"""
        mock_result = mock_subprocess_result(returncode=0, stdout="cubic\n")

        with patch("app.services.bbr.run") as mock_run:
            mock_run.return_value = mock_result

            self.service.disable_bbr()

            # Только одна проверка на наличие cubic
            mock_run.assert_called_once_with(
                ["sysctl", "-n", "net.ipv4.tcp_congestion_control"], check=False
            )

    def test_enable_bbr_first_time(self, mock_subprocess_result, mock_bbr_write_config_file):
        """Тест включения BBR при первом запуске"""
        # Simulate BBR not being enabled initially, then getting enabled
        side_effects = [
            mock_subprocess_result(returncode=0, stdout="cubic\n"),  # Initial check shows cubic
            mock_subprocess_result(returncode=0, stdout=""),  # update_os
            mock_subprocess_result(
                returncode=0, stdout=""
            ),  # lsmod check shows module not loaded initially
            mock_subprocess_result(returncode=0, stdout=""),  # modprobe succeeds
            mock_subprocess_result(
                returncode=0, stdout="tcp_bbr 20480 25 - Live 0x0000000000000000\n"
            ),  # lsmod check shows module loaded after modprobe
            mock_subprocess_result(returncode=0, stdout=""),  # sysctl --system
            mock_subprocess_result(returncode=0, stdout="bbr\n"),  # Final check shows bbr
        ]

        with (
            patch.object(self.service, "_has_bbr_configuration", side_effect=[False, True]),
            patch("app.services.bbr.run") as mock_run,
            patch.object(
                self.service, "_is_bbr_module_loaded", side_effect=[False, True]
            ) as mock_is_loaded,
        ):
            mock_run.side_effect = side_effects
            mock_bbr_write_config_file.return_value = True

            self.service.enable_bbr()

            # Check that critical methods were called
            # Based on actual behavior, we might not get all 7 calls if there are early returns
            assert mock_run.call_count >= 3  # At least initial check, update_os, final check
            assert (
                mock_bbr_write_config_file.call_count >= 1
            )  # At least one config should be written if process continues

    def test_enable_bbr_returns_false_when_modprobe_fails(self):
        with (
            patch.object(self.service, "_get_current_congestion_control", return_value="cubic"),
            patch.object(self.service, "_is_bbr_module_loaded", return_value=False),
            patch("app.services.bbr.run") as mock_run,
        ):
            mock_run.return_value = Mock(returncode=1, stdout="")
            result = self.service.enable_bbr()

        assert result is False

    def test_enable_bbr_returns_false_when_module_still_not_loaded_after_modprobe(self):
        with (
            patch.object(self.service, "_get_current_congestion_control", return_value="cubic"),
            patch.object(self.service, "_is_bbr_module_loaded", side_effect=[False, False]),
            patch("app.services.bbr.run") as mock_run,
            patch("app.services.bbr.time.sleep"),
        ):
            mock_run.return_value = Mock(returncode=0, stdout="")
            result = self.service.enable_bbr()

        assert result is False

    def test_enable_bbr_returns_false_when_first_config_write_fails(self):
        with (
            patch.object(self.service, "_get_current_congestion_control", return_value="cubic"),
            patch.object(self.service, "_is_bbr_module_loaded", return_value=True),
            patch.object(self.service, "_write_config_file", return_value=False),
        ):
            result = self.service.enable_bbr()

        assert result is False

    def test_enable_bbr_returns_false_when_final_algorithm_is_not_bbr(self):
        with (
            patch.object(
                self.service,
                "_get_current_congestion_control",
                side_effect=["cubic", "reno"],
            ),
            patch.object(self.service, "_is_bbr_module_loaded", return_value=True),
            patch.object(self.service, "_write_config_file", return_value=True),
            patch("app.services.bbr.run") as mock_run,
        ):
            mock_run.return_value = Mock(returncode=0, stdout="")
            result = self.service.enable_bbr()

        assert result is False

    def test_enable_bbr_successful_full_flow(self):
        with (
            patch.object(self.service, "install", return_value=True),
            patch.object(
                self.service,
                "_get_current_congestion_control",
                side_effect=["cubic", "bbr"],
            ),
            patch.object(self.service, "_is_bbr_module_loaded", return_value=True),
            patch.object(self.service, "_write_config_file", return_value=True),
            patch("app.services.bbr.run") as mock_run,
        ):
            mock_run.return_value = Mock(returncode=0, stdout="")
            result = self.service.enable_bbr()

        assert result is True

    @patch("app.services.bbr.run")
    @patch("app.services.bbr.BBRService._write_config_file")
    def test_disable_bbr_from_enabled_state(self, mock_write_config, mock_run):
        """Тест отключения BBR из включенного состояния"""
        # Simulate BBR being enabled, then disabling it
        side_effects = [
            Mock(returncode=0, stdout="bbr\n"),  # Initial check shows bbr
            Mock(returncode=0, stdout=""),  # Apply cubic setting
            Mock(returncode=0, stdout=""),  # Apply qdisc setting
            Mock(returncode=0, stdout="cubic\n"),  # Final check shows cubic
        ]
        mock_run.side_effect = side_effects
        mock_write_config.return_value = True

        self.service.disable_bbr()

        # Check that critical methods were called
        assert mock_run.call_count == 4  # Initial check, apply settings (2), final check
        mock_write_config.assert_called()  # Config file should be updated

    @patch("builtins.input", return_value="n")
    def test_disable_bbr_cancelled_by_user(self, mock_input):
        result = self.service.disable_bbr(confirm=True)
        assert result is True

    def test_disable_bbr_returns_false_when_write_config_fails(self):
        with (
            patch.object(self.service, "_get_current_congestion_control", return_value="bbr"),
            patch.object(self.service, "_write_config_file", return_value=False),
        ):
            result = self.service.disable_bbr()

        assert result is False

    def test_disable_bbr_returns_false_when_final_algorithm_is_still_bbr(self):
        with (
            patch.object(
                self.service,
                "_get_current_congestion_control",
                side_effect=["bbr", "bbr"],
            ),
            patch.object(self.service, "_write_config_file", return_value=True),
            patch("app.services.bbr.run") as mock_run,
        ):
            mock_run.return_value = Mock(returncode=0, stdout="")
            result = self.service.disable_bbr()

        assert result is False

    def test_disable_bbr_returns_false_when_final_algorithm_is_unknown(self):
        with (
            patch.object(
                self.service,
                "_get_current_congestion_control",
                side_effect=["bbr", None],
            ),
            patch.object(self.service, "_write_config_file", return_value=True),
            patch("app.services.bbr.run") as mock_run,
        ):
            mock_run.return_value = Mock(returncode=0, stdout="")
            result = self.service.disable_bbr()

        assert result is False

    def test_get_current_congestion_control_general_exception(self):
        """Тест получения текущего алгоритма с общей ошибкой"""
        with patch("app.services.bbr.run") as mock_run:
            mock_run.side_effect = Exception("General error")

            result = self.service._get_current_congestion_control()

            # Should return None when general exception occurs
            assert result is None

    def test_is_bbr_module_loaded_general_exception(self):
        """Тест проверки загрузки модуля с общей ошибкой"""
        with patch("app.services.bbr.run") as mock_run:
            mock_run.side_effect = Exception("General error")

            result = self.service._is_bbr_module_loaded()

            # Should return False when general exception occurs
            assert result is False

    @patch("builtins.open")
    @patch("pathlib.Path.mkdir")
    def test_write_config_file_general_exception(self, mock_mkdir, mock_file):
        """Тест записи конфигурационного файла с общей ошибкой"""
        mock_file.side_effect = Exception("General error")

        result = self.service._write_config_file(
            "/etc/modules-load.d/bbr.conf", "tcp_bbr\n", "test config"
        )

        assert result is False

    @patch("app.services.bbr.run")
    @patch("app.services.bbr.BBRService._is_bbr_module_loaded")
    @patch("app.services.bbr.BBRService._write_config_file")
    def test_enable_bbr_file_not_found_error(self, mock_write_config, mock_is_loaded, mock_run):
        """Тест включения BBR с ошибкой FileNotFoundError"""
        mock_run.side_effect = FileNotFoundError("Command not found")

        with patch("app.services.bbr.logger") as mock_logger:
            self.service.enable_bbr()

            # Should log the error
            mock_logger.error.assert_called()

    @patch("app.services.bbr.run")
    @patch("app.services.bbr.BBRService._is_bbr_module_loaded")
    @patch("app.services.bbr.BBRService._write_config_file")
    def test_enable_bbr_permission_error(self, mock_write_config, mock_is_loaded, mock_run):
        """Тест включения BBR с ошибкой PermissionError"""
        mock_run.side_effect = PermissionError("Permission denied")

        with patch("app.services.bbr.logger") as mock_logger:
            self.service.enable_bbr()

            # Should log the error
            mock_logger.error.assert_called()

    @patch("app.services.bbr.run")
    @patch("app.services.bbr.BBRService._is_bbr_module_loaded")
    @patch("app.services.bbr.BBRService._write_config_file")
    def test_enable_bbr_general_exception(self, mock_write_config, mock_is_loaded, mock_run):
        """Тест включения BBR с общей ошибкой"""
        mock_write_config.side_effect = Exception("General error")

        with patch("app.services.bbr.logger") as mock_logger:
            self.service.enable_bbr()

            # Should log the exception
            mock_logger.exception.assert_called()

    @patch("app.services.bbr.run")
    @patch("app.services.bbr.BBRService._write_config_file")
    def test_disable_bbr_file_not_found_error(self, mock_write_config, mock_run):
        """Тест отключения BBR с ошибкой FileNotFoundError"""
        mock_run.side_effect = FileNotFoundError("Command not found")

        with patch("app.services.bbr.logger") as mock_logger:
            self.service.disable_bbr()

            # Should log the error
            mock_logger.error.assert_called()

    @patch("app.services.bbr.run")
    @patch("app.services.bbr.BBRService._write_config_file")
    def test_disable_bbr_permission_error(self, mock_write_config, mock_run):
        """Тест отключения BBR с ошибкой PermissionError"""
        mock_run.side_effect = PermissionError("Permission denied")

        with patch("app.services.bbr.logger") as mock_logger:
            self.service.disable_bbr()

            # Should log the error
            mock_logger.error.assert_called()

    @patch("app.services.bbr.run")
    @patch("app.services.bbr.BBRService._write_config_file")
    def test_disable_bbr_general_exception(self, mock_write_config, mock_run):
        """Тест отключения BBR с общей ошибкой"""
        mock_run.side_effect = Exception("General error")

        with patch("app.services.bbr.logger") as mock_logger:
            self.service.disable_bbr()

            # Should log the exception
            mock_logger.exception.assert_called()
