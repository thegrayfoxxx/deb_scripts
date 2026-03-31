import subprocess

from app.utils.logger import get_logger
from app.utils.status_text import format_status_snapshot
from app.utils.subprocess_utils import run

logger = get_logger(__name__)


class DockerService:
    INFO_LINES = (
        "Docker — платформа для контейнеризации приложений и сервисов",
        "Основные преимущества:",
        "• Изоляция приложений в легковесных контейнерах",
        "• Упрощение процесса развертывания",
        "• Совместимость между различными системами",
        "• Быстрый запуск и остановка сервисов",
        "• Эффективное использование ресурсов",
        "🔗 Официальный сайт: https://docker.com",
    )

    def _get_docker_version(self) -> str | None | bool:
        """Возвращает версию Docker, если установлен, иначе None"""
        try:
            logger.debug("🔍 Проверка: docker --version")
            result = run(["docker", "--version"], check=False)
            if result.returncode == 0:
                try:
                    version = result.stdout.strip()
                except Exception as e:
                    logger.debug(f"❌ Ошибка при обработке вывода docker --version: {e}")
                    return None
                logger.debug(f"✅ Docker найден: {version}")
                return version
            logger.debug(f"❌ docker --version вернул код {result.returncode}")
            return None
        except FileNotFoundError:
            logger.debug("❌ Команда docker не найдена в PATH")
            return False

    def is_installed(self) -> bool:
        """Проверяет, установлен ли Docker."""
        return bool(self._get_docker_version())

    def get_status(self) -> str:
        """Возвращает человекочитаемый статус Docker."""
        version = self._get_docker_version()
        if version:
            return format_status_snapshot(
                installed=True,
                details=[f"Версия Docker: {version}"],
            )
        return format_status_snapshot(installed=False)

    def get_info_lines(self) -> tuple[str, ...]:
        """Возвращает краткую информацию о сервисе для интерактивного UI."""
        return self.INFO_LINES

    def install(self) -> bool:
        """Устанавливает Docker Engine"""
        try:
            logger.info("🐳 Начало установки Docker Engine...")

            logger.debug("🔍 Проверка наличия Docker Engine...")
            if version := self._get_docker_version():
                logger.info(f"✅ Docker Engine уже установлен: {version} 🎉")
                return True

            logger.debug("📦 Установка утилиты curl для загрузки скрипта...")
            curl_result = run(["apt", "install", "-y", "curl"], check=False)
            logger.debug(f"📋 apt install curl вывод:\n{curl_result.stdout.strip()}")
            if curl_result.returncode != 0:
                logger.warning("⚠️ curl уже установлен или возникла незначительная ошибка")

            logger.info("⬇️ Запуск официального установщика Docker...")
            download_result = run(
                ["curl", "-fsSL", "https://get.docker.com", "-o", "get-docker.sh"],
                check=False,
            )
            if download_result.returncode != 0:
                logger.error("❌ Не удалось скачать скрипт установки Docker")
                return False
            logger.debug("✅ Скрипт загружен")

            logger.debug("🔧 Запуск установки Docker Engine через официальный скрипт...")
            install_result = run(["sh", "./get-docker.sh"], check=False)
            logger.debug(f"📋 get-docker.sh вывод:\n{install_result.stdout.strip()}")
            if install_result.returncode != 0:
                logger.error("❌ Ошибка при выполнении скрипта установки Docker")
                return False

            logger.debug("🧹 Очистка временных файлов после установки...")
            run(["rm", "./get-docker.sh"], check=False)
            logger.debug("✅ get-docker.sh удалён")

            logger.debug("🔍 Финальная проверка установки...")
            if version := self._get_docker_version():
                logger.info(f"✅ Docker Engine успешно установлен! {version} 🎉")
                return True

            logger.error("❌ Docker Engine не обнаружен после завершения установки")
            return False

        except FileNotFoundError as e:
            logger.error(f"📁 Команда не найдена: {e}")
            return False
        except PermissionError as e:
            logger.error(f"🔐 Ошибка прав доступа (требуется root?): {e}")
            return False
        except Exception:
            logger.exception("💥 Критическая ошибка при установке Docker")
            return False

    def uninstall(self, confirm: bool = False) -> bool:
        """Полностью удаляет Docker Engine и данные (идемпотентно)"""
        try:
            if confirm:
                confirmation = input(
                    "⚠️ Вы уверены, что хотите удалить Docker Engine и все его данные (включая контейнеры, образы и тома)? (y/N): "
                )
                if confirmation.lower() not in ["y", "yes"]:
                    logger.info("❌ Удаление Docker отменено пользователем")
                    return True

            logger.warning("⚠️ Начало удаления Docker Engine...")
            logger.warning("⚠️ Все контейнеры, образы и тома будут безвозвратно удалены!")

            logger.debug("🔍 Проверка наличия Docker Engine...")
            if not self._get_docker_version():
                logger.info("✅ Docker Engine не установлен, пропускаем удаление 🧹")
                run(["rm", "-f", "/etc/apt/sources.list.d/docker.list"], check=False)
                run(["rm", "-f", "/etc/apt/keyrings/docker.asc"], check=False)
                logger.debug("✅ Конфигурационные файлы удалены")
                return True

            logger.debug("🗑️ Удаление пакетов Docker Engine...")
            try:
                purge_result = run(
                    [
                        "apt",
                        "purge",
                        "--auto-remove",
                        "-y",
                        "docker-ce",
                        "docker-ce-cli",
                        "containerd.io",
                        "docker-buildx-plugin",
                        "docker-compose-plugin",
                        "docker-ce-rootless-extras",
                    ]
                )
                logger.debug(f"📋 apt purge вывод:\n{purge_result.stdout.strip()}")
                logger.debug("✅ Пакеты Docker Engine успешно удалены")
            except subprocess.CalledProcessError as e:
                if e.returncode == 100:
                    logger.info("✅ Пакеты Docker Engine уже удалены или не были установлены")
                else:
                    logger.warning("⚠️ Удаление пакетов Docker завершилось с предупреждением")
                    logger.debug(f"apt purge stderr: {e.stderr.strip()}")

            logger.debug("🧹 Удаление данных Docker Engine (контейнеры, образы, тома)...")
            docker_data = run(["rm", "-rf", "/var/lib/docker"], check=False)
            logger.debug(
                f"🗑️ /var/lib/docker: {'удалено' if docker_data.returncode == 0 else 'ошибка'}"
            )

            containerd_data = run(["rm", "-rf", "/var/lib/containerd"], check=False)
            logger.debug(
                f"🗑️ /var/lib/containerd: {'удалено' if containerd_data.returncode == 0 else 'ошибка'}"
            )

            logger.debug("🧹 Очистка конфигурационных файлов Docker Engine...")
            run(["rm", "-f", "/etc/apt/sources.list.d/docker.list"], check=False)
            run(["rm", "-f", "/etc/apt/keyrings/docker.asc"], check=False)
            logger.debug("✅ Конфигурационные файлы удалены")

            logger.debug("🔍 Проверка успешного удаления Docker Engine...")
            if not self._get_docker_version():
                logger.info("✅ Docker Engine полностью удален 🧹")
                return True

            logger.warning("⚠️ Docker Engine всё ещё обнаружен в системе")
            return False

        except PermissionError as e:
            logger.error(f"🔐 Ошибка прав доступа (требуется root?): {e}")
            return False
        except Exception:
            logger.exception("💥 Критическая ошибка при удалении Docker")
            return False
