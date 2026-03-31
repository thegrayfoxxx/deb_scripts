import subprocess

from app.bootstrap.logger import get_logger
from app.core.status import format_status_snapshot
from app.core.subprocess import run
from app.i18n.locale import is_affirmative_reply, t, tr

logger = get_logger(__name__)


class DockerService:
    def _get_docker_version(self) -> str | None | bool:
        """Возвращает версию Docker, если установлен, иначе None"""
        try:
            logger.debug(tr("🔍 Проверка: docker --version", "🔍 Checking: docker --version"))
            result = run(["docker", "--version"], check=False)
            if result.returncode == 0:
                try:
                    version = result.stdout.strip()
                except Exception as e:
                    logger.debug(
                        tr(
                            f"❌ Ошибка при обработке вывода docker --version: {e}",
                            f"❌ Error while processing docker --version output: {e}",
                        )
                    )
                    return None
                logger.debug(tr(f"✅ Docker найден: {version}", f"✅ Docker found: {version}"))
                return version
            logger.debug(
                tr(
                    f"❌ docker --version вернул код {result.returncode}",
                    f"❌ docker --version returned code {result.returncode}",
                )
            )
            return None
        except FileNotFoundError:
            logger.debug(
                tr("❌ Команда docker не найдена в PATH", "❌ docker command not found in PATH")
            )
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
                details=[t("status.docker_version", version=version)],
            )
        return format_status_snapshot(installed=False)

    def get_info_lines(self) -> tuple[str, ...]:
        """Возвращает краткую информацию о сервисе для интерактивного UI."""
        return (
            t("info.docker.line1"),
            t("info.docker.line2"),
            t("info.docker.line3"),
            t("info.docker.line4"),
            t("info.docker.line5"),
            t("info.docker.line6"),
            t("info.docker.line7"),
            t("info.docker.line8"),
        )

    def install(self) -> bool:
        """Устанавливает Docker Engine"""
        try:
            logger.info(
                tr(
                    "🐳 Начало установки Docker Engine...",
                    "🐳 Starting Docker Engine installation...",
                )
            )

            logger.debug(
                tr(
                    "🔍 Проверка наличия Docker Engine...",
                    "🔍 Checking whether Docker Engine is installed...",
                )
            )
            if version := self._get_docker_version():
                logger.info(
                    tr(
                        f"✅ Docker Engine уже установлен: {version} 🎉",
                        f"✅ Docker Engine is already installed: {version} 🎉",
                    )
                )
                return True

            logger.debug(
                tr(
                    "📦 Установка утилиты curl для загрузки скрипта...",
                    "📦 Installing curl to download the script...",
                )
            )
            curl_result = run(["apt", "install", "-y", "curl"], check=False)
            logger.debug(
                tr(
                    f"📋 apt install curl вывод:\n{curl_result.stdout.strip()}",
                    f"📋 apt install curl output:\n{curl_result.stdout.strip()}",
                )
            )
            if curl_result.returncode != 0:
                logger.warning(
                    tr(
                        "⚠️ curl уже установлен или возникла незначительная ошибка",
                        "⚠️ curl is already installed or a minor issue occurred",
                    )
                )

            logger.info(
                tr(
                    "⬇️ Запуск официального установщика Docker...",
                    "⬇️ Running the official Docker installer...",
                )
            )
            download_result = run(
                ["curl", "-fsSL", "https://get.docker.com", "-o", "get-docker.sh"],
                check=False,
            )
            if download_result.returncode != 0:
                logger.error(
                    tr(
                        "❌ Не удалось скачать скрипт установки Docker",
                        "❌ Failed to download the Docker installation script",
                    )
                )
                return False
            logger.debug(tr("✅ Скрипт загружен", "✅ Script downloaded"))

            logger.debug(
                tr(
                    "🔧 Запуск установки Docker Engine через официальный скрипт...",
                    "🔧 Running Docker Engine installation via the official script...",
                )
            )
            install_result = run(["sh", "./get-docker.sh"], check=False)
            logger.debug(
                tr(
                    f"📋 get-docker.sh вывод:\n{install_result.stdout.strip()}",
                    f"📋 get-docker.sh output:\n{install_result.stdout.strip()}",
                )
            )
            if install_result.returncode != 0:
                logger.error(
                    tr(
                        "❌ Ошибка при выполнении скрипта установки Docker",
                        "❌ Error while running the Docker installation script",
                    )
                )
                return False

            logger.debug(
                tr(
                    "🧹 Очистка временных файлов после установки...",
                    "🧹 Cleaning temporary files after installation...",
                )
            )
            run(["rm", "./get-docker.sh"], check=False)
            logger.debug(tr("✅ get-docker.sh удалён", "✅ get-docker.sh removed"))

            logger.debug(
                tr("🔍 Финальная проверка установки...", "🔍 Final installation check...")
            )
            if version := self._get_docker_version():
                logger.info(
                    tr(
                        f"✅ Docker Engine успешно установлен! {version} 🎉",
                        f"✅ Docker Engine installed successfully! {version} 🎉",
                    )
                )
                return True

            logger.error(
                tr(
                    "❌ Docker Engine не обнаружен после завершения установки",
                    "❌ Docker Engine was not detected after installation",
                )
            )
            return False

        except FileNotFoundError as e:
            logger.error(tr(f"📁 Команда не найдена: {e}", f"📁 Command not found: {e}"))
            return False
        except PermissionError as e:
            logger.error(
                tr(
                    f"🔐 Ошибка прав доступа (требуется root?): {e}",
                    f"🔐 Permission error (is root required?): {e}",
                )
            )
            return False
        except Exception:
            logger.exception(
                tr(
                    "💥 Критическая ошибка при установке Docker",
                    "💥 Critical error during Docker installation",
                )
            )
            return False

    def uninstall(self, confirm: bool = False) -> bool:
        """Полностью удаляет Docker Engine и данные (идемпотентно)"""
        try:
            if confirm:
                confirmation = input(
                    tr(
                        "⚠️ Вы уверены, что хотите удалить Docker Engine и все его данные (включая контейнеры, образы и тома)? ",
                        "⚠️ Are you sure you want to remove Docker Engine and all its data (including containers, images, and volumes)? ",
                    )
                    + t("common.confirm_yes_no")
                )
                if not is_affirmative_reply(confirmation):
                    logger.info(
                        tr(
                            "❌ Удаление Docker отменено пользователем",
                            "❌ Docker removal was cancelled by the user",
                        )
                    )
                    return True

            logger.warning(
                tr("⚠️ Начало удаления Docker Engine...", "⚠️ Starting Docker Engine removal...")
            )
            logger.warning(
                tr(
                    "⚠️ Все контейнеры, образы и тома будут безвозвратно удалены!",
                    "⚠️ All containers, images, and volumes will be permanently removed!",
                )
            )

            logger.debug(
                tr(
                    "🔍 Проверка наличия Docker Engine...",
                    "🔍 Checking whether Docker Engine is installed...",
                )
            )
            if not self._get_docker_version():
                logger.info(
                    tr(
                        "✅ Docker Engine не установлен, пропускаем удаление 🧹",
                        "✅ Docker Engine is not installed, skipping removal 🧹",
                    )
                )
                run(["rm", "-f", "/etc/apt/sources.list.d/docker.list"], check=False)
                run(["rm", "-f", "/etc/apt/keyrings/docker.asc"], check=False)
                logger.debug(
                    tr("✅ Конфигурационные файлы удалены", "✅ Configuration files removed")
                )
                return True

            logger.debug(
                tr("🗑️ Удаление пакетов Docker Engine...", "🗑️ Removing Docker Engine packages...")
            )
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
                logger.debug(
                    tr(
                        f"📋 apt purge вывод:\n{purge_result.stdout.strip()}",
                        f"📋 apt purge output:\n{purge_result.stdout.strip()}",
                    )
                )
                logger.debug(
                    tr(
                        "✅ Пакеты Docker Engine успешно удалены",
                        "✅ Docker Engine packages removed successfully",
                    )
                )
            except subprocess.CalledProcessError as e:
                if e.returncode == 100:
                    logger.info(
                        tr(
                            "✅ Пакеты Docker Engine уже удалены или не были установлены",
                            "✅ Docker Engine packages are already removed or were never installed",
                        )
                    )
                else:
                    logger.warning(
                        tr(
                            "⚠️ Удаление пакетов Docker завершилось с предупреждением",
                            "⚠️ Docker package removal finished with a warning",
                        )
                    )
                    logger.debug(
                        tr(
                            f"apt purge stderr: {e.stderr.strip()}",
                            f"apt purge stderr: {e.stderr.strip()}",
                        )
                    )

            logger.debug(
                tr(
                    "🧹 Удаление данных Docker Engine (контейнеры, образы, тома)...",
                    "🧹 Removing Docker Engine data (containers, images, volumes)...",
                )
            )
            docker_data = run(["rm", "-rf", "/var/lib/docker"], check=False)
            logger.debug(
                f"🗑️ /var/lib/docker: {'удалено' if docker_data.returncode == 0 else 'ошибка'}"
            )

            containerd_data = run(["rm", "-rf", "/var/lib/containerd"], check=False)
            logger.debug(
                f"🗑️ /var/lib/containerd: {'удалено' if containerd_data.returncode == 0 else 'ошибка'}"
            )

            logger.debug(
                tr(
                    "🧹 Очистка конфигурационных файлов Docker Engine...",
                    "🧹 Cleaning Docker Engine configuration files...",
                )
            )
            run(["rm", "-f", "/etc/apt/sources.list.d/docker.list"], check=False)
            run(["rm", "-f", "/etc/apt/keyrings/docker.asc"], check=False)
            logger.debug(tr("✅ Конфигурационные файлы удалены", "✅ Configuration files removed"))

            logger.debug(
                tr(
                    "🔍 Проверка успешного удаления Docker Engine...",
                    "🔍 Verifying Docker Engine removal...",
                )
            )
            if not self._get_docker_version():
                logger.info(
                    tr(
                        "✅ Docker Engine полностью удален 🧹",
                        "✅ Docker Engine was fully removed 🧹",
                    )
                )
                return True

            logger.warning(
                tr(
                    "⚠️ Docker Engine всё ещё обнаружен в системе",
                    "⚠️ Docker Engine is still detected on the system",
                )
            )
            return False

        except PermissionError as e:
            logger.error(
                tr(
                    f"🔐 Ошибка прав доступа (требуется root?): {e}",
                    f"🔐 Permission error (is root required?): {e}",
                )
            )
            return False
        except Exception:
            logger.exception(
                tr(
                    "💥 Критическая ошибка при удалении Docker",
                    "💥 Critical error during Docker removal",
                )
            )
            return False
