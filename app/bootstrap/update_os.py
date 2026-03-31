from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.bootstrap.logger import get_logger
from app.core.subprocess import run

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
    logger.debug("🔍 Проверка доступных обновлений (apt list --upgradable)...")
    result = run(["apt", "list", "--upgradable"], check=False)
    logger.debug(f"📋 apt list --upgradable вывод:\n{result.stdout.strip()}")

    if result.returncode != 0:
        logger.warning("⚠️ Не удалось проверить список обновляемых пакетов")
        return False

    return bool(_parse_upgradable_packages(result.stdout))


def update_os() -> None:
    """Обновляет индексы пакетов по TTL и выполняет upgrade только при наличии обновлений."""
    try:
        logger.info("🔄 Проверка обновлений ОС...")

        now = datetime.now(UTC)
        last_update_time = _get_last_update_time()

        if _should_refresh_package_lists(now, last_update_time):
            logger.debug("📦 Обновление списков пакетов (apt update)...")
            update_result = run(["apt", "update", "-y"], check=False)
            logger.debug(f"📋 apt update вывод:\n{update_result.stdout.strip()}")

            if update_result.returncode != 0:
                logger.error("❌ Ошибка при обновлении списков пакетов")
                return
        else:
            logger.info("ℹ️ Списки пакетов ещё свежие, apt update пропущен")

        if not _has_upgradable_packages():
            logger.info("✅ Обновлений не найдено")
            return

        logger.info("⬆️ Найдены обновления, запускаю apt upgrade...")
        upgrade_result = run(["apt", "upgrade", "-y"], check=False)
        logger.debug(f"📋 apt upgrade вывод:\n{upgrade_result.stdout.strip()}")

        if upgrade_result.returncode != 0:
            logger.error("❌ Ошибка при установке обновлений")
            return

        logger.info("✅ ОС успешно обновлена")

    except FileNotFoundError as e:
        logger.error(f"📁 Команда не найдена (проверьте наличие apt): {e}")
    except PermissionError as e:
        logger.error(f"🔐 Ошибка прав доступа (требуется root?): {e}")
    except Exception:
        logger.exception("💥 Критическая ошибка при обновлении ОС")
