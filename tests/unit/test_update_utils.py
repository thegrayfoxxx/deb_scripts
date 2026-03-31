"""Тесты для модуля app.bootstrap.update_os"""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

from app.bootstrap.update_os import (
    APT_UPDATE_MAX_AGE,
    _get_last_update_time,
    _has_upgradable_packages,
    _parse_upgradable_packages,
    _path_mtime,
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

    def test_parse_upgradable_packages_ignores_localized_banner(self):
        output = "Вывод списка…\npackage-a/stable 1.2 amd64 [upgradable from: 1.1]\n"

        assert _parse_upgradable_packages(output) == [
            "package-a/stable 1.2 amd64 [upgradable from: 1.1]"
        ]

    def test_path_mtime_returns_none_when_path_does_not_exist(self):
        assert _path_mtime(Path("/missing/file")) is None

    def test_path_mtime_returns_none_on_os_error(self):
        fake_path = Mock(spec=Path)
        fake_path.exists.return_value = True
        fake_path.stat.side_effect = OSError("boom")

        assert _path_mtime(fake_path) is None

    def test_get_last_update_time_uses_stamp_file_when_available(self):
        expected = datetime(2026, 4, 1, 12, 0, tzinfo=UTC)

        with patch("app.bootstrap.update_os._path_mtime", return_value=expected):
            assert _get_last_update_time() == expected

    def test_get_last_update_time_returns_none_when_lists_dir_is_missing(self):
        with (
            patch("app.bootstrap.update_os._path_mtime", return_value=None),
            patch("app.bootstrap.update_os.APT_LISTS_DIR") as mock_lists_dir,
        ):
            mock_lists_dir.exists.return_value = False

            assert _get_last_update_time() is None

    def test_get_last_update_time_falls_back_to_latest_lists_mtime(self):
        list_a = Mock(spec=Path)
        list_a.is_file.return_value = True
        list_a.name = "deb.debian.org_main"
        list_a.stat.return_value = Mock(st_mtime=10)

        list_b = Mock(spec=Path)
        list_b.is_file.return_value = True
        list_b.name = "security_main"
        list_b.stat.return_value = Mock(st_mtime=20)

        lock_file = Mock(spec=Path)
        lock_file.is_file.return_value = True
        lock_file.name = "lock"

        with (
            patch("app.bootstrap.update_os._path_mtime", return_value=None),
            patch("app.bootstrap.update_os.APT_LISTS_DIR") as mock_lists_dir,
        ):
            mock_lists_dir.exists.return_value = True
            mock_lists_dir.iterdir.return_value = [list_a, list_b, lock_file]

            result = _get_last_update_time()

        assert result == datetime.fromtimestamp(20, tz=UTC)

    def test_get_last_update_time_returns_none_on_lists_dir_os_error(self):
        with (
            patch("app.bootstrap.update_os._path_mtime", return_value=None),
            patch("app.bootstrap.update_os.APT_LISTS_DIR") as mock_lists_dir,
        ):
            mock_lists_dir.exists.return_value = True
            mock_lists_dir.iterdir.side_effect = OSError("boom")

            assert _get_last_update_time() is None

    def test_has_upgradable_packages_returns_false_on_non_zero_exit(self, mock_subprocess_result):
        result = mock_subprocess_result(returncode=1, stdout="")

        with patch("app.bootstrap.update_os.run", return_value=result):
            assert _has_upgradable_packages() is False

    def test_has_upgradable_packages_returns_true_when_packages_exist(
        self, mock_subprocess_result
    ):
        result = mock_subprocess_result(
            returncode=0, stdout="Listing...\nopenssl/stable 3.0 amd64 [upgradable from: 2.9]"
        )

        with patch("app.bootstrap.update_os.run", return_value=result):
            assert _has_upgradable_packages() is True

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

    def test_update_os_does_not_run_upgrade_when_only_localized_banner_is_present(
        self, mock_subprocess_result
    ):
        upgradable_result = mock_subprocess_result(returncode=0, stdout="Вывод списка…\n")

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
