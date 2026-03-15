import subprocess

from app.utils.logger import get_logger
from app.utils.subprocess_utils import run
from app.utils.update_utils import update_os

logger = get_logger(__name__)


class DockerService:
    def _get_docker_version(self) -> str | None | bool:
        """Возвращает версию Docker, если установлен, иначе None"""
        try:
            logger.debug("🔍 Проверка: docker --version")
            result = run(["docker", "--version"], check=False)
            if result.returncode == 0:
                version = result.stdout.strip()
                logger.debug(f"✅ Docker найден: {version}")
                return version
            logger.debug(f"❌ docker --version вернул код {result.returncode}")
            return None
        except FileNotFoundError:
            logger.debug("❌ Команда docker не найдена в PATH")
            return False

    def install_docker(self):
        """Устанавливает Docker Engine"""
        try:
            logger.info("🐳 Начало установки Docker...")

            # 🔍 Проверка: а может, Docker уже установлен?
            logger.info("🔍 Проверка наличия Docker...")
            if version := self._get_docker_version():
                logger.info(f"✅ Docker уже установлен: {version} 🎉")
                return

            # Шаг 1: Обновление ОС
            logger.info("🔄 Обновление системы...")
            update_os()
            logger.debug("✅ Система обновлена")

            # Шаг 2: Установка curl (если нет)
            logger.info("📦 Установка curl...")
            curl_result = run(["apt", "install", "-y", "curl"], check=False)
            logger.debug(f"📋 apt install curl вывод:\n{curl_result.stdout.strip()}")
            if curl_result.returncode != 0:
                logger.warning("⚠️ curl уже установлен или возникла незначительная ошибка")

            # Шаг 3: Скачивание скрипта установки
            logger.info("⬇️ Скачивание официального скрипта get-docker.sh...")
            # ✅ Исправлено: убраны пробелы в URL
            download_result = run(
                ["curl", "-fsSL", "https://get.docker.com", "-o", "get-docker.sh"], check=False
            )
            if download_result.returncode != 0:
                logger.error("❌ Не удалось скачать скрипт установки Docker")
                return
            logger.debug("✅ Скрипт загружен")

            # Шаг 4: Запуск установки
            logger.info("🔧 Запуск установки Docker...")
            install_result = run(["sh", "./get-docker.sh"], check=False)
            logger.debug(f"📋 get-docker.sh вывод:\n{install_result.stdout.strip()}")
            if install_result.returncode != 0:
                logger.error("❌ Ошибка при выполнении скрипта установки Docker")
                return

            # Шаг 5: Очистка
            logger.info("🧹 Очистка временных файлов...")
            run(["rm", "./get-docker.sh"], check=False)
            logger.debug("✅ get-docker.sh удалён")

            # Шаг 6: Финальная проверка установки
            logger.info("🔍 Финальная проверка установки...")
            if version := self._get_docker_version():
                logger.info(f"✅ Docker успешно установлен! {version} 🎉")
            else:
                logger.error("❌ Docker не обнаружен после установки")

        except FileNotFoundError as e:
            logger.error(f"📁 Команда не найдена: {e}")
        except PermissionError as e:
            logger.error(f"🔐 Ошибка прав доступа (требуется root?): {e}")
        except Exception:
            logger.exception("💥 Критическая ошибка при установке Docker")

    def uninstall_docker(self):
        """Полностью удаляет Docker Engine и данные"""
        try:
            logger.warning("⚠️ Начало удаления Docker...")
            logger.warning("⚠️ Все контейнеры, образы и тома будут безвозвратно удалены!")

            # 🔍 Проверка: а установлен ли Docker вообще?
            logger.info("🔍 Проверка наличия Docker...")
            if not self._get_docker_version():
                logger.info("✅ Docker не установлен, пропускаем удаление 🧹")
                # Чистим конфиги и выходим
                run(["rm", "-f", "/etc/apt/sources.list.d/docker.list"], check=False)
                run(["rm", "-f", "/etc/apt/keyrings/docker.asc"], check=False)
                logger.debug("✅ Конфигурационные файлы удалены")
                return

            # Шаг 1: Удаление пакетов (с обработкой "уже не установлен")
            logger.info("🗑️ Удаление пакетов Docker...")
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
                logger.info("✅ Пакеты Docker удалены")
            except subprocess.CalledProcessError as e:
                if e.returncode == 100:
                    logger.info("✅ Пакеты Docker уже удалены или не были установлены")
                else:
                    logger.warning(
                        f"⚠️ Предупреждение при удалении пакетов (код {e.returncode}): {e.stderr.strip()}"
                    )

            # Шаг 2: Удаление данных Docker
            logger.info("🧹 Удаление данных Docker...")
            docker_data = run(["rm", "-rf", "/var/lib/docker"], check=False)
            logger.debug(
                f"🗑️ /var/lib/docker: {'удалено' if docker_data.returncode == 0 else 'ошибка'}"
            )

            containerd_data = run(["rm", "-rf", "/var/lib/containerd"], check=False)
            logger.debug(
                f"🗑️ /var/lib/containerd: {'удалено' if containerd_data.returncode == 0 else 'ошибка'}"
            )

            # Шаг 3: Очистка конфигов (всегда в конце)
            logger.info("🧹 Очистка конфигурационных файлов...")
            run(["rm", "-f", "/etc/apt/sources.list.d/docker.list"], check=False)
            run(["rm", "-f", "/etc/apt/keyrings/docker.asc"], check=False)
            logger.debug("✅ Конфигурационные файлы удалены")

            # Шаг 4: Проверка удаления
            logger.info("🔍 Проверка удаления...")
            if not self._get_docker_version():
                logger.info("✅ Docker полностью удален 🧹")
            else:
                logger.warning("⚠️ Docker всё ещё обнаружен в системе")

        except PermissionError as e:
            logger.error(f"🔐 Ошибка прав доступа (требуется root?): {e}")
        except Exception:
            logger.exception("💥 Критическая ошибка при удалении Docker")
