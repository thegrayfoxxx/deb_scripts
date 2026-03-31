from pathlib import Path

from app.bootstrap.logger import get_logger
from app.core.status import format_status_snapshot
from app.core.subprocess import run
from app.i18n.locale import is_affirmative_reply, t, tr

logger = get_logger(__name__)


class UVService:
    # 🔧 Константы: пути и конфигурация
    UV_INSTALL_URL = "https://astral.sh/uv/install.sh"
    UV_BIN_PATH = Path.home() / ".local" / "bin"
    UV_EXECUTABLE = UV_BIN_PATH / "uv"
    UVX_EXECUTABLE = UV_BIN_PATH / "uvx"
    ENV_FILE = Path.home() / ".local" / "bin" / "env"

    # 🔧 Команды для проверки
    UV_VERSION_CMD = ["uv", "--version"]
    UV_PYTHON_DIR_CMD = ["uv", "python", "dir"]
    UV_TOOL_DIR_CMD = ["uv", "tool", "dir"]
    UV_CACHE_CLEAN_CMD = ["uv", "cache", "clean"]

    def _get_uv_command(self, *args: str) -> list[str]:
        """Возвращает команду uv, даже если ~/.local/bin ещё не в PATH."""
        executable = self.UV_EXECUTABLE if self.UV_EXECUTABLE.exists() else "uv"
        return [str(executable), *args]

    def _is_uv_installed(self) -> bool:
        """Проверяет, установлен ли uv в системе"""
        try:
            logger.debug(tr("🔍 Проверка наличия uv...", "🔍 Checking whether uv is installed..."))
            result = run(self._get_uv_command("--version"), check=False)
            if result.returncode == 0:
                version = result.stdout.strip()
                logger.debug(tr(f"✅ uv найден: {version}", f"✅ uv found: {version}"))
                return True
            logger.debug(
                tr(
                    f"❌ uv --version вернул код {result.returncode}",
                    f"❌ uv --version returned code {result.returncode}",
                )
            )
            return False
        except FileNotFoundError:
            logger.debug(tr("❌ Команда uv не найдена в PATH", "❌ uv command not found in PATH"))
            return False
        except Exception as e:
            logger.debug(tr(f"❌ Ошибка при проверке uv: {e}", f"❌ Error while checking uv: {e}"))
            return False

    def _get_uv_paths(self) -> dict[str, str] | None:
        """
        Получает пути к директориям uv (python, tool).
        Returns: dict с путями или None при ошибке
        """
        try:
            logger.debug(tr("🔍 Получение путей uv...", "🔍 Retrieving uv paths..."))

            python_result = run(self._get_uv_command("python", "dir"), check=False)
            tool_result = run(self._get_uv_command("tool", "dir"), check=False)

            if python_result.returncode == 0 and tool_result.returncode == 0:
                paths = {
                    "python": python_result.stdout.strip(),
                    "tool": tool_result.stdout.strip(),
                }
                logger.debug(tr(f"📁 Пути uv: {paths}", f"📁 uv paths: {paths}"))
                return paths
            logger.debug(
                tr(
                    f"❌ Ошибка получения путей: python={python_result.returncode}, tool={tool_result.returncode}",
                    f"❌ Failed to retrieve paths: python={python_result.returncode}, tool={tool_result.returncode}",
                )
            )
            return None
        except Exception as e:
            logger.debug(
                tr(f"❌ Ошибка при получении путей: {e}", f"❌ Error while retrieving paths: {e}")
            )
            return None

    def _is_path_configured(self) -> bool:
        """Проверяет, есть ли ~/.local/bin в PATH текущего процесса."""
        import os

        home_local_bin = str(Path.home() / ".local" / "bin")
        current_path = os.environ.get("PATH", "")

        if home_local_bin in current_path:
            logger.debug(tr("✅ ~/.local/bin уже в PATH", "✅ ~/.local/bin is already in PATH"))
            return True

        logger.debug(
            tr(
                "⚠️ ~/.local/bin не найден в PATH текущего процесса",
                "⚠️ ~/.local/bin is not in the current process PATH",
            )
        )
        return False

    def _warn_about_missing_path(self) -> None:
        """Показывает пользователю краткую подсказку по настройке PATH."""
        home_local_bin = str(Path.home() / ".local" / "bin")

        logger.warning(
            tr(
                "⚠️ ~/.local/bin не в PATH. Добавьте в ~/.bashrc или ~/.zshrc:",
                "⚠️ ~/.local/bin is not in PATH. Add it to ~/.bashrc or ~/.zshrc:",
            )
        )
        logger.warning(f'   export PATH="{home_local_bin}:$PATH"')
        logger.warning(
            tr(
                "ℹ️ После этого выполните: source ~/.bashrc (или перезапустите терминал)",
                "ℹ️ After that, run: source ~/.bashrc (or restart the terminal)",
            )
        )

    def is_installed(self) -> bool:
        """Проверяет, установлен ли uv."""
        return self._is_uv_installed()

    def get_status(self) -> str:
        """Возвращает человекочитаемый статус uv."""
        if not self._is_uv_installed():
            return format_status_snapshot(installed=False)

        version_result = run(self._get_uv_command("--version"), check=False)
        version = version_result.stdout.strip() if version_result.returncode == 0 else "unknown"
        path_ok = self._is_path_configured()
        return format_status_snapshot(
            installed=True,
            details=[
                t("status.uv_version", version=version),
                t("status.path_configured_yes" if path_ok else "status.path_configured_no"),
            ],
        )

    def get_info_lines(self) -> tuple[str, ...]:
        """Возвращает краткую информацию о сервисе для интерактивного UI."""
        return (
            t("info.uv.line1"),
            t("info.uv.line2"),
            t("info.uv.line3"),
            t("info.uv.line4"),
            t("info.uv.line5"),
            t("info.uv.line6"),
            t("info.uv.line7"),
            t("info.uv.line8"),
            t("info.uv.line9"),
            t("info.uv.line10"),
        )

    def install(self) -> bool:
        """Устанавливает uv (идемпотентно: безопасно запускать много раз)"""
        try:
            logger.info(
                tr(
                    "🐍 Начало установки uv (современного менеджера пакетов Python)...",
                    "🐍 Starting uv installation (modern Python package manager)...",
                )
            )

            logger.debug(
                tr(
                    "🔍 Проверка наличия uv в системе...",
                    "🔍 Checking whether uv is installed on the system...",
                )
            )
            if self._is_uv_installed():
                version_result = run(self._get_uv_command("--version"), check=False)
                version = version_result.stdout.strip()
                logger.info(
                    tr(
                        f"✅ uv уже установлен: {version} 🎉",
                        f"✅ uv is already installed: {version} 🎉",
                    )
                )
                if not self._is_path_configured():
                    self._warn_about_missing_path()
                return True

            logger.debug(
                tr(
                    "📦 Проверка наличия утилиты curl для загрузки установщика...",
                    "📦 Checking whether curl is available to download the installer...",
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
                    "⬇️ Запуск официального установщика uv...",
                    "⬇️ Running the official uv installer...",
                )
            )
            download_result = run(
                ["curl", "-LsSf", self.UV_INSTALL_URL, "-o", "uv_install.sh"],
                check=False,
            )
            if download_result.returncode != 0:
                logger.error(
                    tr(
                        "❌ Не удалось скачать скрипт установки uv",
                        "❌ Failed to download the uv installation script",
                    )
                )
                return False
            logger.debug(tr("✅ Скрипт загружен", "✅ Script downloaded"))

            logger.debug(
                tr(
                    "🔧 Запуск установки uv в неинтерактивном режиме...",
                    "🔧 Running uv installation in non-interactive mode...",
                )
            )
            install_result = run(
                ["sh", "./uv_install.sh"],
                check=False,
                env={"UV_UNINSTALL": "0"},
            )
            logger.debug(
                tr(
                    f"📋 uv install вывод:\n{install_result.stdout.strip()}",
                    f"📋 uv install output:\n{install_result.stdout.strip()}",
                )
            )

            if install_result.returncode != 0:
                logger.error(
                    tr(
                        "❌ Ошибка при выполнении скрипта установки uv",
                        "❌ Error while running the uv installation script",
                    )
                )
                return False
            logger.debug(tr("✅ Скрипт установки завершён", "✅ Installation script finished"))

            logger.debug(
                tr(
                    "🧹 Очистка временных файлов после установки uv...",
                    "🧹 Cleaning temporary files after uv installation...",
                )
            )
            run(["rm", "-f", "uv_install.sh"], check=False)
            logger.debug(tr("✅ uv_install.sh удалён", "✅ uv_install.sh removed"))

            logger.debug(
                tr(
                    "🔍 Финальная проверка успешной установки uv...",
                    "🔍 Final check of successful uv installation...",
                )
            )
            if self._is_uv_installed():
                version_result = run(self._get_uv_command("--version"), check=False)
                version = version_result.stdout.strip()
                logger.info(
                    tr(
                        f"✅ uv успешно установлен! {version} 🎉",
                        f"✅ uv installed successfully! {version} 🎉",
                    )
                )
                if not self._is_path_configured():
                    self._warn_about_missing_path()
                return True

            logger.error(
                tr(
                    "❌ uv не обнаружен после установки",
                    "❌ uv was not detected after installation",
                )
            )
            logger.warning(
                tr(
                    "💡 Проверьте, что ~/.local/bin добавлен в PATH текущего пользователя",
                    "💡 Make sure ~/.local/bin is added to the current user's PATH",
                )
            )
            return False

        except FileNotFoundError as e:
            logger.error(tr(f"📁 Команда не найдена: {e}", f"📁 Command not found: {e}"))
            return False
        except PermissionError as e:
            logger.error(tr(f"🔐 Ошибка прав доступа: {e}", f"🔐 Permission error: {e}"))
            return False
        except Exception:
            logger.exception(
                tr(
                    "💥 Критическая ошибка при установке uv",
                    "💥 Critical error during uv installation",
                )
            )
            return False

    def uninstall(self, confirm: bool = False) -> bool:
        """Полностью удаляет uv и его данные (идемпотентно)"""
        try:
            if confirm:
                confirmation = input(
                    tr(
                        "⚠️ Вы уверены, что хотите удалить uv и все его данные? ",
                        "⚠️ Are you sure you want to remove uv and all its data? ",
                    )
                    + t("common.confirm_yes_no")
                )
                if not is_affirmative_reply(confirmation):
                    logger.info(
                        tr(
                            "❌ Удаление uv отменено пользователем",
                            "❌ uv removal was cancelled by the user",
                        )
                    )
                    return True

            logger.warning(
                tr(
                    "⚠️ Начало удаления uv (современного менеджера пакетов Python)...",
                    "⚠️ Starting uv removal (modern Python package manager)...",
                )
            )

            logger.debug(
                tr(
                    "🔍 Проверка наличия uv в системе...",
                    "🔍 Checking whether uv is installed on the system...",
                )
            )
            if not self._is_uv_installed():
                logger.info(
                    tr(
                        "✅ uv не установлен, пропускаем удаление 🧹",
                        "✅ uv is not installed, skipping removal 🧹",
                    )
                )
                run(
                    ["rm", "-f", str(self.UV_EXECUTABLE), str(self.UVX_EXECUTABLE)],
                    check=False,
                )
                return True

            logger.debug(
                tr(
                    "🧹 Очистка кэша uv (временные файлы и зависимости)...",
                    "🧹 Cleaning uv cache (temporary files and dependencies)...",
                )
            )
            cache_result = run(self._get_uv_command("cache", "clean"), check=False)
            logger.debug(
                tr(
                    f"📋 uv cache clean вывод:\n{cache_result.stdout.strip()}",
                    f"📋 uv cache clean output:\n{cache_result.stdout.strip()}",
                )
            )
            if cache_result.returncode == 0:
                logger.debug(tr("✅ Кэш очищен", "✅ Cache cleaned"))
            else:
                logger.warning(
                    tr(
                        "⚠️ Не удалось очистить кэш (возможно, уже пуст)",
                        "⚠️ Failed to clean the cache (it may already be empty)",
                    )
                )

            logger.debug(
                tr(
                    "🔍 Получение путей к директориям данных uv...",
                    "🔍 Retrieving paths to uv data directories...",
                )
            )
            paths = self._get_uv_paths()

            if paths:
                logger.debug(
                    tr(
                        f"🗑️ Удаление директории Python: {paths['python']}...",
                        f"🗑️ Removing Python directory: {paths['python']}...",
                    )
                )
                python_result = run(["rm", "-rf", paths["python"]], check=False)
                logger.debug(
                    f"🗑️ Python dir: {'удалено' if python_result.returncode == 0 else 'ошибка'}"
                )

                logger.debug(
                    tr(
                        f"🗑️ Удаление директории инструментов: {paths['tool']}...",
                        f"🗑️ Removing tools directory: {paths['tool']}...",
                    )
                )
                tool_result = run(["rm", "-rf", paths["tool"]], check=False)
                logger.debug(
                    f"🗑️ Tool dir: {'удалено' if tool_result.returncode == 0 else 'ошибка'}"
                )
            else:
                logger.warning(
                    tr(
                        "⚠️ Не удалось получить пути uv, пропускаем удаление директорий",
                        "⚠️ Failed to get uv paths, skipping directory removal",
                    )
                )

            logger.debug(
                tr(
                    "🧹 Удаление исполняемых файлов uv и uvx...",
                    "🧹 Removing uv and uvx executables...",
                )
            )
            bin_result = run(
                ["rm", "-f", str(self.UV_EXECUTABLE), str(self.UVX_EXECUTABLE)],
                check=False,
            )
            logger.debug(
                tr(
                    f"🗑️ Исполняемые файлы: {'удалено' if bin_result.returncode == 0 else 'ошибка'}",
                    (f"🗑️ Executables: {'removed' if bin_result.returncode == 0 else 'error'}"),
                )
            )

            if self.ENV_FILE.exists():
                logger.debug(tr("🧹 Очистка env-файла...", "🧹 Cleaning env file..."))
                run(["rm", "-f", str(self.ENV_FILE)], check=False)
                logger.debug(tr(f"✅ Удалён {self.ENV_FILE}", f"✅ Removed {self.ENV_FILE}"))

            logger.debug(
                tr(
                    "🔍 Финальная проверка полного удаления uv из системы...",
                    "🔍 Final verification of complete uv removal from the system...",
                )
            )
            if not self._is_uv_installed():
                logger.info(tr("✅ uv полностью удалён 🧹", "✅ uv was fully removed 🧹"))
                return True

            logger.warning(
                tr("⚠️ uv всё ещё обнаружен в системе", "⚠️ uv is still detected on the system")
            )
            logger.warning(
                tr(
                    "💡 Попробуйте удалить вручную: rm -rf ~/.local/bin/uv ~/.local/bin/uvx",
                    "💡 Try removing it manually: rm -rf ~/.local/bin/uv ~/.local/bin/uvx",
                )
            )
            return False

        except FileNotFoundError:
            logger.info(
                tr(
                    "✅ uv уже удалён (команда не найдена) 🧹",
                    "✅ uv is already removed (command not found) 🧹",
                )
            )
            return True
        except PermissionError as e:
            logger.error(tr(f"🔐 Ошибка прав доступа: {e}", f"🔐 Permission error: {e}"))
            return False
        except Exception:
            logger.exception(
                tr("💥 Критическая ошибка при удалении uv", "💥 Critical error during uv removal")
            )
            return False
