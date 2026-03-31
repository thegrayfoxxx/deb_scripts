"""Тесты для модуля app.bootstrap.update_os"""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from app.bootstrap.update_os import (
    APT_UPDATE_MAX_AGE,
    _parse_upgradable_packages,
    _should_refresh_package_lists,
    update_os,
)


class TestUpdateUtils:
    """Тесты для утилит обновления системы"""

    def test_should_refresh_package_lists_when_last_update_is_missing(self):
        now = datetime(2026, 4, 1, 12, 0, tzinfo=UTC)

        assert _should_refresh_package_lists(now, None) is True

    def test_should_refresh_package_lists_when_last_update_is_fresh(self):
        now = datetime(2026, 4, 1, 12, 0, tzinfo=UTC)
        last_update_time = now - (APT_UPDATE_MAX_AGE - timedelta(minutes=1))

        assert _should_refresh_package_lists(now, last_update_time) is False

    def test_should_refresh_package_lists_when_last_update_is_stale(self):
        now = datetime(2026, 4, 1, 12, 0, tzinfo=UTC)
        last_update_time = now - (APT_UPDATE_MAX_AGE + timedelta(minutes=1))

        assert _should_refresh_package_lists(now, last_update_time) is True

    def test_parse_upgradable_packages_ignores_listing_banner(self):
        output = "Listing...\npackage-a/stable 1.2 amd64 [upgradable from: 1.1]\n"

        assert _parse_upgradable_packages(output) == [
            "package-a/stable 1.2 amd64 [upgradable from: 1.1]"
        ]

    def test_update_os_skips_apt_update_when_package_lists_are_fresh(self, mock_subprocess_result):
        upgradable_result = mock_subprocess_result(returncode=0, stdout="Listing...\n")

        with (
            patch(
                "app.bootstrap.update_os._get_last_update_time",
                return_value=datetime.now(UTC),
            ),
            patch("app.bootstrap.update_os.run", return_value=upgradable_result) as mock_run,
            patch("app.bootstrap.update_os.logger") as mock_logger,
        ):
            update_os()

        mock_run.assert_called_once_with(["apt", "list", "--upgradable"], check=False)
        mock_logger.info.assert_any_call("ℹ️ Списки пакетов ещё свежие, apt update пропущен")
        mock_logger.info.assert_any_call("✅ Обновлений не найдено")

    def test_update_os_runs_apt_update_when_package_lists_are_stale(self, mock_subprocess_result):
        update_result = mock_subprocess_result(returncode=0, stdout="Get:1 Debian updates")
        upgradable_result = mock_subprocess_result(returncode=0, stdout="Listing...\n")

        with (
            patch(
                "app.bootstrap.update_os._get_last_update_time",
                return_value=datetime.now(UTC) - (APT_UPDATE_MAX_AGE + timedelta(minutes=1)),
            ),
            patch("app.bootstrap.update_os.run") as mock_run,
            patch("app.bootstrap.update_os.logger") as mock_logger,
        ):
            mock_run.side_effect = [update_result, upgradable_result]
            update_os()

        assert mock_run.call_count == 2
        mock_run.assert_any_call(["apt", "update", "-y"], check=False)
        mock_run.assert_any_call(["apt", "list", "--upgradable"], check=False)
        mock_logger.debug.assert_any_call("📦 Обновление списков пакетов (apt update)...")

    def test_update_os_runs_upgrade_only_when_updates_exist(self, mock_subprocess_result):
        upgradable_result = mock_subprocess_result(
            returncode=0, stdout="Listing...\nopenssl/stable 3.0 amd64 [upgradable from: 2.9]"
        )
        upgrade_result = mock_subprocess_result(returncode=0, stdout="Setting up openssl...")

        with (
            patch(
                "app.bootstrap.update_os._get_last_update_time",
                return_value=datetime.now(UTC),
            ),
            patch("app.bootstrap.update_os.run") as mock_run,
            patch("app.bootstrap.update_os.logger") as mock_logger,
        ):
            mock_run.side_effect = [upgradable_result, upgrade_result]
            update_os()

        assert mock_run.call_count == 2
        mock_run.assert_any_call(["apt", "list", "--upgradable"], check=False)
        mock_run.assert_any_call(["apt", "upgrade", "-y"], check=False)
        mock_logger.info.assert_any_call("⬆️ Найдены обновления, запускаю apt upgrade...")
        mock_logger.info.assert_any_call("✅ ОС успешно обновлена")

    def test_update_os_does_not_run_upgrade_when_no_updates_exist(self, mock_subprocess_result):
        upgradable_result = mock_subprocess_result(returncode=0, stdout="Listing...\n")

        with (
            patch(
                "app.bootstrap.update_os._get_last_update_time",
                return_value=datetime.now(UTC),
            ),
            patch("app.bootstrap.update_os.run", return_value=upgradable_result) as mock_run,
            patch("app.bootstrap.update_os.logger") as mock_logger,
        ):
            update_os()

        mock_run.assert_called_once_with(["apt", "list", "--upgradable"], check=False)
        mock_logger.info.assert_any_call("✅ Обновлений не найдено")

    def test_update_os_update_failed(self, mock_subprocess_result):
        update_result = mock_subprocess_result(returncode=1, stderr="Failed to fetch updates")

        with (
            patch("app.bootstrap.update_os._get_last_update_time", return_value=None),
            patch("app.bootstrap.update_os.run", return_value=update_result) as mock_run,
            patch("app.bootstrap.update_os.logger") as mock_logger,
        ):
            update_os()

        mock_run.assert_called_once_with(["apt", "update", "-y"], check=False)
        mock_logger.error.assert_any_call("❌ Ошибка при обновлении списков пакетов")

    def test_update_os_upgrade_failed(self, mock_subprocess_result):
        upgradable_result = mock_subprocess_result(
            returncode=0, stdout="Listing...\npackage-a/stable 1.2 amd64 [upgradable from: 1.1]"
        )
        upgrade_result = mock_subprocess_result(returncode=1, stderr="Upgrade failed")

        with (
            patch(
                "app.bootstrap.update_os._get_last_update_time",
                return_value=datetime.now(UTC),
            ),
            patch("app.bootstrap.update_os.run") as mock_run,
            patch("app.bootstrap.update_os.logger") as mock_logger,
        ):
            mock_run.side_effect = [upgradable_result, upgrade_result]
            update_os()

        mock_run.assert_any_call(["apt", "upgrade", "-y"], check=False)
        mock_logger.error.assert_any_call("❌ Ошибка при установке обновлений")

    def test_update_os_file_not_found_error(self):
        with (
            patch("app.bootstrap.update_os._get_last_update_time", return_value=None),
            patch(
                "app.bootstrap.update_os.run",
                side_effect=FileNotFoundError("apt command not found"),
            ),
            patch("app.bootstrap.update_os.logger") as mock_logger,
        ):
            update_os()

        mock_logger.error.assert_called_with(
            "📁 Команда не найдена (проверьте наличие apt): apt command not found"
        )

    def test_update_os_permission_error(self):
        with (
            patch("app.bootstrap.update_os._get_last_update_time", return_value=None),
            patch("app.bootstrap.update_os.run", side_effect=PermissionError("Permission denied")),
            patch("app.bootstrap.update_os.logger") as mock_logger,
        ):
            update_os()

        mock_logger.error.assert_called_with(
            "🔐 Ошибка прав доступа (требуется root?): Permission denied"
        )

    def test_update_os_general_exception(self):
        with (
            patch("app.bootstrap.update_os._get_last_update_time", return_value=None),
            patch("app.bootstrap.update_os.run", side_effect=Exception("General error occurred")),
            patch("app.bootstrap.update_os.logger") as mock_logger,
        ):
            update_os()

        mock_logger.exception.assert_called_with("💥 Критическая ошибка при обновлении ОС")
