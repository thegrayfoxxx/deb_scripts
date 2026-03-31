from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.bootstrap.logger import get_logger
from app.core.subprocess import run
from app.i18n.locale import t, tr

logger = get_logger(__name__)

APT_UPDATE_MAX_AGE = timedelta(hours=6)
APT_UPDATE_SUCCESS_STAMP = Path("/var/lib/apt/periodic/update-success-stamp")
APT_LISTS_DIR = Path("/var/lib/apt/lists")


def _path_mtime(path: Path) -> datetime | None:
    try:
        if not path.exists():
            return None
        return datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
    except OSError:
        return None


def _get_last_update_time() -> datetime | None:
    """Возвращает время последнего успешного обновления индекса пакетов."""
    stamp_time = _path_mtime(APT_UPDATE_SUCCESS_STAMP)
    if stamp_time is not None:
        return stamp_time

    try:
        if not APT_LISTS_DIR.exists():
            return None
        mtimes = [
            datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
            for path in APT_LISTS_DIR.iterdir()
            if path.is_file() and path.name not in {"lock"}
        ]
    except OSError:
        return None

    return max(mtimes, default=None)


def _should_refresh_package_lists(
    now: datetime, last_update_time: datetime | None, max_age: timedelta = APT_UPDATE_MAX_AGE
) -> bool:
    """Определяет, нужно ли выполнять apt update."""
    if last_update_time is None:
        return True
    return now - last_update_time >= max_age


def _parse_upgradable_packages(output: str) -> list[str]:
    """Возвращает список обновляемых пакетов из вывода apt list --upgradable."""
    packages: list[str] = []
    for line in output.splitlines():
        normalized = line.strip()
        if not normalized:
            continue
        # Строки пакетов у apt list --upgradable имеют устойчивую форму:
        # package/repo version arch [upgradable from: ...]
        if "/" not in normalized or "[" not in normalized:
            continue
        packages.append(normalized)
    return packages


def _has_upgradable_packages() -> bool:
    """Проверяет, есть ли пакеты для apt upgrade."""
    logger.debug(
        tr(
            "🔍 Проверка доступных обновлений (apt list --upgradable)...",
            "🔍 Checking available updates (apt list --upgradable)...",
        )
    )
    result = run(["apt", "list", "--upgradable"], check=False)
    logger.debug(
        tr(
            f"📋 apt list --upgradable вывод:\n{result.stdout.strip()}",
            f"📋 apt list --upgradable output:\n{result.stdout.strip()}",
        )
    )

    if result.returncode != 0:
        logger.warning(t("update.upgradable_check_failed"))
        return False

    return bool(_parse_upgradable_packages(result.stdout))


def update_os() -> None:
    """Обновляет индексы пакетов по TTL и выполняет upgrade только при наличии обновлений."""
    try:
        logger.info(t("update.start"))

        now = datetime.now(UTC)
        last_update_time = _get_last_update_time()

        if _should_refresh_package_lists(now, last_update_time):
            logger.debug(
                tr(
                    "📦 Обновление списков пакетов (apt update)...",
                    "📦 Refreshing package lists (apt update)...",
                )
            )
            update_result = run(["apt", "update", "-y"], check=False)
            logger.debug(
                tr(
                    f"📋 apt update вывод:\n{update_result.stdout.strip()}",
                    f"📋 apt update output:\n{update_result.stdout.strip()}",
                )
            )

            if update_result.returncode != 0:
                logger.error(t("update.refresh_failed"))
                return
        else:
            logger.info(t("update.refresh_skipped"))

        if not _has_upgradable_packages():
            logger.info(t("update.no_updates"))
            return

        logger.info(t("update.upgrade_start"))
        upgrade_result = run(["apt", "upgrade", "-y"], check=False)
        logger.debug(
            tr(
                f"📋 apt upgrade вывод:\n{upgrade_result.stdout.strip()}",
                f"📋 apt upgrade output:\n{upgrade_result.stdout.strip()}",
            )
        )

        if upgrade_result.returncode != 0:
            logger.error(t("update.upgrade_failed"))
            return

        logger.info(t("update.success"))

    except FileNotFoundError as e:
        logger.error(t("update.command_not_found", error=e))
    except PermissionError as e:
        logger.error(t("update.permission_error", error=e))
    except Exception:
        logger.exception(t("update.fatal_error"))
