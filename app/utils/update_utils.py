from app.utils.logger import get_logger
from app.utils.subprocess_utils import run

logger = get_logger(__name__)


def update_os():
    """Обновляет пакеты операционной системы"""
    try:
        logger.info("🔄 Начало обновления ОС...")

        # Шаг 1: Обновление списков пакетов
        logger.info("📦 Обновление списков пакетов (apt update)...")
        update_result = run(["apt", "update", "-y"])
        logger.debug(f"📋 apt update вывод:\n{update_result.stdout.strip()}")

        if update_result.returncode != 0:
            logger.error("❌ Ошибка при обновлении списков пакетов")
            return

        # Шаг 2: Установка обновлений
        logger.info("⬇️ Установка обновлений (apt upgrade)...")
        upgrade_result = run(["apt", "upgrade", "-y"])
        logger.debug(f"📋 apt upgrade вывод:\n{upgrade_result.stdout.strip()}")

        if upgrade_result.returncode != 0:
            logger.error("❌ Ошибка при установке обновлений")
            return

        # Успешное завершение
        logger.info("✅ ОС успешно обновлена 🎉")

    except FileNotFoundError:
        logger.error("📁 Команда не найдена (проверьте наличие apt): {e}")
    except PermissionError:
        logger.error("🔐 Ошибка прав доступа (требуется root?): {e}")
    except Exception:
        logger.exception("💥 Критическая ошибка при обновлении ОС")
