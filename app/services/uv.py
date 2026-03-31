import os
import shutil
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
    GLOBAL_BIN_PATH = Path("/usr/local/bin")
    UV_EXECUTABLE = UV_BIN_PATH / "uv"
    UVX_EXECUTABLE = UV_BIN_PATH / "uvx"
    UVW_EXECUTABLE = UV_BIN_PATH / "uvw"
    GLOBAL_UV_EXECUTABLE = GLOBAL_BIN_PATH / "uv"
    GLOBAL_UVX_EXECUTABLE = GLOBAL_BIN_PATH / "uvx"
    GLOBAL_UVW_EXECUTABLE = GLOBAL_BIN_PATH / "uvw"
    ENV_FILE = Path.home() / ".local" / "bin" / "env"

    # 🔧 Команды для проверки
    UV_VERSION_CMD = ["uv", "--version"]
    UV_PYTHON_DIR_CMD = ["uv", "python", "dir"]
    UV_TOOL_DIR_CMD = ["uv", "tool", "dir"]
    UV_CACHE_CLEAN_CMD = ["uv", "cache", "clean"]

    def _get_shell_env(self) -> dict[str, str]:
        """Возвращает env для shell-команд с HOME эффективного пользователя."""
        return {**os.environ, "HOME": str(Path.home())}

    def _source_uv_env(self) -> bool:
        """Подгружает ~/.local/bin/env в PATH текущего процесса, если файл существует."""
        if not self.ENV_FILE.exists():
            logger.debug(tr("ℹ️ uv env-файл не найден", "ℹ️ uv env file was not found"))
            return False

        source_result = run(
            ["bash", "-lc", f'source "{self.ENV_FILE}" && printf "%s" "$PATH"'],
            check=False,
            env=self._get_shell_env(),
        )
        if source_result.returncode != 0:
            logger.warning(
                tr(
                    "⚠️ Не удалось загрузить uv env-файл",
                    "⚠️ Failed to load the uv env file",
                )
            )
            return False

        updated_path = source_result.stdout.strip()
        if updated_path:
            os.environ["PATH"] = updated_path
            logger.debug(
                tr("✅ PATH обновлён из uv env", "✅ PATH updated from uv env")
            )
            return True

        logger.warning(
            tr(
                "⚠️ uv env-файл не вернул PATH",
                "⚠️ The uv env file did not return a PATH value",
            )
        )
        return False

    def _resolve_uv_executable(self) -> Path | None:
        """Возвращает фактический путь к uv, если бинарник можно определить."""
        if self.UV_EXECUTABLE.exists():
            return self.UV_EXECUTABLE

        detected_uv = shutil.which("uv")
        if detected_uv:
            return Path(detected_uv)

        return None

    def _get_uv_binaries_from_path(self) -> tuple[Path, ...]:
        """Собирает все uv/uvx/uvw, которые реально лежат в каталогах PATH."""
        discovered: set[Path] = set()
        path_value = os.environ.get("PATH", "")

        for raw_dir in path_value.split(":"):
            if not raw_dir:
                continue

            bin_dir = Path(raw_dir)
            for binary_name in ("uv", "uvx", "uvw"):
                binary_path = bin_dir / binary_name
                if binary_path.exists():
                    discovered.add(binary_path)

        return tuple(sorted(discovered, key=lambda path: str(path)))

    def _get_global_uv_symlink_pairs(self) -> tuple[tuple[Path, Path], ...]:
        """Возвращает пары source->link для глобальной публикации uv."""
        return (
            (self.UV_EXECUTABLE, self.GLOBAL_UV_EXECUTABLE),
            (self.UVX_EXECUTABLE, self.GLOBAL_UVX_EXECUTABLE),
            (self.UVW_EXECUTABLE, self.GLOBAL_UVW_EXECUTABLE),
        )

    def _ensure_global_uv_symlinks(self) -> bool:
        """Создаёт симлинки в /usr/local/bin для глобального вызова uv."""
        ok = True

        for source_path, link_path in self._get_global_uv_symlink_pairs():
            if not source_path.exists():
                continue

            try:
                if link_path.is_symlink():
                    if link_path.resolve(strict=False) == source_path.resolve(
                        strict=False
                    ):
                        continue
                    logger.warning(
                        tr(
                            f"⚠️ Симлинк {link_path} уже указывает на другой файл",
                            f"⚠️ The symlink {link_path} already points to another file",
                        )
                    )
                    ok = False
                    continue

                if link_path.exists():
                    logger.warning(
                        tr(
                            f"⚠️ Файл {link_path} уже существует и не является симлинком",
                            f"⚠️ The file {link_path} already exists and is not a symlink",
                        )
                    )
                    ok = False
                    continue

                link_path.parent.mkdir(parents=True, exist_ok=True)
                link_path.symlink_to(source_path)
            except OSError as exc:
                logger.warning(
                    tr(
                        f"⚠️ Не удалось создать симлинк {link_path}: {exc}",
                        f"⚠️ Failed to create the symlink {link_path}: {exc}",
                    )
                )
                ok = False

        return ok

    def _remove_owned_global_uv_symlinks(self) -> bool:
        """Удаляет только те глобальные симлинки, которые указывают на локальный uv."""
        ok = True

        for source_path, link_path in self._get_global_uv_symlink_pairs():
            try:
                if not link_path.is_symlink():
                    continue

                if link_path.resolve(strict=False) != source_path.resolve(strict=False):
                    logger.warning(
                        tr(
                            f"⚠️ Симлинк {link_path} не принадлежит текущей установке uv",
                            f"⚠️ The symlink {link_path} does not belong to the current uv installation",
                        )
                    )
                    ok = False
                    continue

                link_path.unlink()
            except OSError as exc:
                logger.warning(
                    tr(
                        f"⚠️ Не удалось удалить симлинк {link_path}: {exc}",
                        f"⚠️ Failed to remove the symlink {link_path}: {exc}",
                    )
                )
                ok = False

        return ok

    def _get_uv_command(self, *args: str) -> list[str]:
        """Возвращает команду uv, даже если ~/.local/bin ещё не в PATH."""
        executable = self._resolve_uv_executable()
        return [str(executable) if executable is not None else "uv", *args]

    def _is_uv_installed(self) -> bool:
        """Проверяет, установлен ли uv в системе"""
        try:
            logger.debug(
                tr(
                    "🔍 Проверка наличия uv...",
                    "🔍 Checking whether uv is installed...",
                )
            )
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
            logger.debug(
                tr("❌ Команда uv не найдена в PATH", "❌ uv command not found in PATH")
            )
            return False
        except Exception as e:
            logger.debug(
                tr(
                    f"❌ Ошибка при проверке uv: {e}",
                    f"❌ Error while checking uv: {e}",
                )
            )
            return False

    def _get_uv_binary_targets(self) -> tuple[Path, ...]:
        """Возвращает набор бинарников uv, которые нужно удалить."""
        targets = {
            self.UV_EXECUTABLE,
            self.UVX_EXECUTABLE,
            self.UVW_EXECUTABLE,
        }
        targets.update(self._get_uv_binaries_from_path())

        resolved_uv = self._resolve_uv_executable()
        if resolved_uv is not None:
            targets.update(
                {
                    resolved_uv,
                    resolved_uv.with_name("uvx"),
                    resolved_uv.with_name("uvw"),
                }
            )

        return tuple(sorted(targets, key=lambda path: str(path)))

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
                tr(
                    f"❌ Ошибка при получении путей: {e}",
                    f"❌ Error while retrieving paths: {e}",
                )
            )
            return None

    def _get_expected_uv_bin_dir(self) -> Path:
        """Возвращает каталог, который должен присутствовать в PATH для найденного uv."""
        resolved_uv = self._resolve_uv_executable()
        if resolved_uv is not None:
            return resolved_uv.parent

        return self.UV_BIN_PATH

    def _is_path_configured(self) -> bool:
        """Проверяет, есть ли каталог найденного uv в PATH текущего процесса."""
        import os

        expected_bin_dir = str(self._get_expected_uv_bin_dir())
        current_path = os.environ.get("PATH", "")
        path_entries = current_path.split(":") if current_path else []

        if expected_bin_dir in path_entries:
            logger.debug(
                tr(
                    f"✅ {expected_bin_dir} уже в PATH",
                    f"✅ {expected_bin_dir} is already in PATH",
                )
            )
            return True

        logger.debug(
            tr(
                f"⚠️ {expected_bin_dir} не найден в PATH текущего процесса",
                f"⚠️ {expected_bin_dir} is not in the current process PATH",
            )
        )
        return False

    def _warn_about_missing_path(self) -> None:
        """Показывает пользователю краткую подсказку по настройке PATH."""
        expected_bin_dir = str(self._get_expected_uv_bin_dir())

        logger.warning(
            tr(
                f"⚠️ {expected_bin_dir} не в PATH. Добавьте в ~/.bashrc или ~/.zshrc:",
                f"⚠️ {expected_bin_dir} is not in PATH. Add it to ~/.bashrc or ~/.zshrc:",
            )
        )
        logger.warning(f'   export PATH="{expected_bin_dir}:$PATH"')
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
        version = (
            version_result.stdout.strip()
            if version_result.returncode == 0
            else "unknown"
        )
        path_ok = self._is_path_configured()
        return format_status_snapshot(
            installed=True,
            details=[
                t("status.uv_version", version=version),
                t(
                    "status.path_configured_yes"
                    if path_ok
                    else "status.path_configured_no"
                ),
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
                self._source_uv_env()
                if not self._ensure_global_uv_symlinks():
                    return False
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
            install_result = run(
                ["bash", "-lc", f"curl -LsSf {self.UV_INSTALL_URL} | sh"],
                check=False,
                env=self._get_shell_env(),
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
            logger.debug(
                tr("✅ Скрипт установки завершён", "✅ Installation script finished")
            )

            logger.debug(
                tr(
                    "🔄 Загрузка uv env-файла в текущий процесс...",
                    "🔄 Loading the uv env file into the current process...",
                )
            )
            self._source_uv_env()
            if not self._ensure_global_uv_symlinks():
                return False

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
            logger.error(
                tr(f"📁 Команда не найдена: {e}", f"📁 Command not found: {e}")
            )
            return False
        except PermissionError as e:
            logger.error(
                tr(f"🔐 Ошибка прав доступа: {e}", f"🔐 Permission error: {e}")
            )
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
                binary_targets = self._get_uv_binary_targets()
                run(
                    ["rm", "-f", *(str(path) for path in binary_targets)],
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

            self._remove_owned_global_uv_symlinks()
            binary_targets = self._get_uv_binary_targets()
            logger.debug(
                tr(
                    "🧹 Удаление исполняемых файлов uv, uvx и uvw...",
                    "🧹 Removing uv, uvx, and uvw executables...",
                )
            )
            bin_result = run(
                ["rm", "-f", *(str(path) for path in binary_targets)],
                check=False,
            )
            logger.debug(
                tr(
                    f"🗑️ Исполняемые файлы: {'удалено' if bin_result.returncode == 0 else 'ошибка'}",
                    (
                        f"🗑️ Executables: {'removed' if bin_result.returncode == 0 else 'error'}"
                    ),
                )
            )

            if self.ENV_FILE.exists():
                logger.debug(tr("🧹 Очистка env-файла...", "🧹 Cleaning env file..."))
                run(["rm", "-f", str(self.ENV_FILE)], check=False)
                logger.debug(
                    tr(f"✅ Удалён {self.ENV_FILE}", f"✅ Removed {self.ENV_FILE}")
                )

            remaining_targets = [
                path
                for path in {*binary_targets, *self._get_uv_binaries_from_path()}
                if path.exists()
            ]
            remaining_uv = shutil.which("uv")

            logger.debug(
                tr(
                    "🔍 Финальная проверка полного удаления uv из системы...",
                    "🔍 Final verification of complete uv removal from the system...",
                )
            )
            if not remaining_targets and remaining_uv is None:
                logger.info(
                    tr("✅ uv полностью удалён 🧹", "✅ uv was fully removed 🧹")
                )
                return True

            if remaining_targets:
                logger.warning(
                    tr(
                        f"⚠️ Остались бинарные файлы uv: {', '.join(str(path) for path in remaining_targets)}",
                        f"⚠️ Remaining uv binaries were found: {', '.join(str(path) for path in remaining_targets)}",
                    )
                )
            if remaining_uv is not None:
                logger.warning(
                    tr(
                        f"⚠️ uv всё ещё обнаружен в PATH: {remaining_uv}",
                        f"⚠️ uv is still detected in PATH: {remaining_uv}",
                    )
                )

            logger.warning(
                tr(
                    "💡 Попробуйте удалить оставшиеся файлы вручную и проверьте PATH",
                    "💡 Try removing the remaining files manually and verify PATH",
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
            logger.error(
                tr(f"🔐 Ошибка прав доступа: {e}", f"🔐 Permission error: {e}")
            )
            return False
        except Exception:
            logger.exception(
                tr(
                    "💥 Критическая ошибка при удалении uv",
                    "💥 Critical error during uv removal",
                )
            )
            return False
