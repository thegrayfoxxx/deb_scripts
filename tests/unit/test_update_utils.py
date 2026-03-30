"""Тесты для модуля app.utils.update_utils"""

from unittest.mock import patch

from app.utils.update_utils import update_os


class TestUpdateUtils:
    """Тесты для утилит обновления системы"""

    def test_update_os_successful(self, mock_subprocess_result):
        """Тест успешного обновления системы"""
        # Подготовка моков
        update_result = mock_subprocess_result(
            returncode=0, stdout="Get:1 Debian Security Updates..."
        )
        upgrade_result = mock_subprocess_result(returncode=0, stdout="Installing updates...")

        with (
            patch("app.utils.update_utils.run") as mock_run,
            patch("app.utils.update_utils.logger") as mock_logger,
        ):
            # Мокаем последовательность вызовов: apt update -> apt upgrade
            mock_run.side_effect = [update_result, upgrade_result]

            # Вызов тестируемой функции
            update_os()

            # Проверяем, что были вызваны нужные команды
            assert mock_run.call_count == 2
            mock_run.assert_any_call(["apt", "update", "-y"])
            mock_run.assert_any_call(["apt", "upgrade", "-y"])

            # Проверяем, что были вызваны логи
            mock_logger.info.assert_any_call("🔄 Начало обновления ОС...")
            mock_logger.debug.assert_any_call("📦 Обновление списков пакетов (apt update)...")
            mock_logger.debug.assert_any_call("⬇️ Установка обновлений (apt upgrade)...")
            mock_logger.info.assert_any_call("✅ ОС успешно обновлена 🎉")

    def test_update_os_update_failed(self, mock_subprocess_result):
        """Тест обновления системы с ошибкой при apt update"""
        # Подготовка мока для провального apt update
        update_result = mock_subprocess_result(returncode=1, stderr="Failed to fetch updates")

        with (
            patch("app.utils.update_utils.run") as mock_run,
            patch("app.utils.update_utils.logger") as mock_logger,
        ):
            mock_run.return_value = update_result

            # Вызов тестируемой функции
            update_os()

            # Проверяем, что была вызвана только команда apt update (не дошло до upgrade)
            mock_run.assert_called_once_with(["apt", "update", "-y"])

            # Проверяем, что были вызваны соответствующие логи
            mock_logger.info.assert_any_call("🔄 Начало обновления ОС...")
            mock_logger.debug.assert_any_call("📦 Обновление списков пакетов (apt update)...")
            mock_logger.error.assert_any_call("❌ Ошибка при обновлении списков пакетов")

    def test_update_os_upgrade_failed(self, mock_subprocess_result):
        """Тест обновления системы с ошибкой при apt upgrade"""
        # Подготовка моков: apt update успешен, но apt upgrade нет
        update_result = mock_subprocess_result(returncode=0, stdout="Successfully updated lists")
        upgrade_result = mock_subprocess_result(returncode=1, stderr="Upgrade failed")

        with (
            patch("app.utils.update_utils.run") as mock_run,
            patch("app.utils.update_utils.logger") as mock_logger,
        ):
            mock_run.side_effect = [update_result, upgrade_result]

            # Вызов тестируемой функции
            update_os()

            # Проверяем, что были вызваны обе команды
            assert mock_run.call_count == 2
            mock_run.assert_any_call(["apt", "update", "-y"])
            mock_run.assert_any_call(["apt", "upgrade", "-y"])

            # Проверяем, что были вызваны соответствующие логи
            mock_logger.info.assert_any_call("🔄 Начало обновления ОС...")
            mock_logger.debug.assert_any_call("📦 Обновление списков пакетов (apt update)...")
            mock_logger.debug.assert_any_call("⬇️ Установка обновлений (apt upgrade)...")
            mock_logger.error.assert_any_call("❌ Ошибка при установке обновлений")

    def test_update_os_file_not_found_error(self):
        """Тест обработки ошибки FileNotFoundError"""
        with (
            patch("app.utils.update_utils.run") as mock_run,
            patch("app.utils.update_utils.logger") as mock_logger,
        ):
            mock_run.side_effect = FileNotFoundError("apt command not found")

            # Вызов тестируемой функции
            update_os()

            # Проверяем, что была записана ошибка
            mock_logger.error.assert_called_with(
                "📁 Команда не найдена (проверьте наличие apt): apt command not found"
            )

    def test_update_os_permission_error(self):
        """Тест обработки ошибки PermissionError"""
        with (
            patch("app.utils.update_utils.run") as mock_run,
            patch("app.utils.update_utils.logger") as mock_logger,
        ):
            mock_run.side_effect = PermissionError("Permission denied")

            # Вызов тестируемой функции
            update_os()

            # Проверяем, что была записана ошибка
            mock_logger.error.assert_called_with(
                "🔐 Ошибка прав доступа (требуется root?): Permission denied"
            )

    def test_update_os_general_exception(self):
        """Тест обработки общей ошибки"""
        with (
            patch("app.utils.update_utils.run") as mock_run,
            patch("app.utils.update_utils.logger") as mock_logger,
        ):
            mock_run.side_effect = Exception("General error occurred")

            # Вызов тестируемой функции
            update_os()

            # Проверяем, что была записана ошибка
            mock_logger.exception.assert_called_with("💥 Критическая ошибка при обновлении ОС")

    def test_update_os_debug_logging(self, mock_subprocess_result):
        """Тест логирования отладочной информации"""
        update_result = mock_subprocess_result(
            returncode=0,
            stdout="Get:1 http://security.debian.org stable/updates/main amd64 Packages [123 kB]",
        )
        upgrade_result = mock_subprocess_result(
            returncode=0, stdout="Setting up package (1.0.0)... Installing..."
        )

        with (
            patch("app.utils.update_utils.run") as mock_run,
            patch("app.utils.update_utils.logger") as mock_logger,
        ):
            mock_run.side_effect = [update_result, upgrade_result]

            # Вызов тестируемой функции
            update_os()

            # Проверяем, что отладочная информация была залогирована
            mock_logger.debug.assert_any_call(
                "📋 apt update вывод:\nGet:1 http://security.debian.org stable/updates/main amd64 Packages [123 kB]"
            )
            mock_logger.debug.assert_any_call(
                "📋 apt upgrade вывод:\nSetting up package (1.0.0)... Installing..."
            )
