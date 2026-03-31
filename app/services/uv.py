from pathlib import Path

from app.utils.logger import get_logger
from app.utils.status_text import format_status_snapshot
from app.utils.subprocess_utils import run

logger = get_logger(__name__)


class UVService:
    INFO_LINES = (
        "UV — современный и быстрый менеджер пакетов Python",
        "Основные преимущества:",
        "• Высокая скорость установки пакетов (в 10-100 раз быстрее, чем pip)",
        "• Современная система разрешения зависимостей",
        "• Альтернатива для pip, pipenv, poetry и других",
        "• Надежная изоляция окружений",
        "• Улучшенная безопасность при установке пакетов",
        "• Полная совместимость с PyPI и системой пакетов Python",
        "🔗 GitHub репозиторий: https://github.com/astral-sh/uv",
        "🔗 Официальный сайт: https://astral.sh",
    )

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
            logger.debug("🔍 Проверка наличия uv...")
            result = run(self._get_uv_command("--version"), check=False)
            if result.returncode == 0:
                version = result.stdout.strip()
                logger.debug(f"✅ uv найден: {version}")
                return True
            logger.debug(f"❌ uv --version вернул код {result.returncode}")
            return False
        except FileNotFoundError:
            logger.debug("❌ Команда uv не найдена в PATH")
            return False
        except Exception as e:
            logger.debug(f"❌ Ошибка при проверке uv: {e}")
            return False

    def _get_uv_paths(self) -> dict[str, str] | None:
        """
        Получает пути к директориям uv (python, tool).
        Returns: dict с путями или None при ошибке
        """
        try:
            logger.debug("🔍 Получение путей uv...")

            python_result = run(self._get_uv_command("python", "dir"), check=False)
            tool_result = run(self._get_uv_command("tool", "dir"), check=False)

            if python_result.returncode == 0 and tool_result.returncode == 0:
                paths = {
                    "python": python_result.stdout.strip(),
                    "tool": tool_result.stdout.strip(),
                }
                logger.debug(f"📁 Пути uv: {paths}")
                return paths
            logger.debug(
                f"❌ Ошибка получения путей: python={python_result.returncode}, tool={tool_result.returncode}"
            )
            return None
        except Exception as e:
            logger.debug(f"❌ Ошибка при получении путей: {e}")
            return None

    def _is_path_configured(self) -> bool:
        """Проверяет, есть ли ~/.local/bin в PATH текущего процесса."""
        import os

        home_local_bin = str(Path.home() / ".local" / "bin")
        current_path = os.environ.get("PATH", "")

        if home_local_bin in current_path:
            logger.debug("✅ ~/.local/bin уже в PATH")
            return True

        logger.debug("⚠️ ~/.local/bin не найден в PATH текущего процесса")
        return False

    def _warn_about_missing_path(self) -> None:
        """Показывает пользователю краткую подсказку по настройке PATH."""
        home_local_bin = str(Path.home() / ".local" / "bin")

        logger.warning("⚠️ ~/.local/bin не в PATH. Добавьте в ~/.bashrc или ~/.zshrc:")
        logger.warning(f'   export PATH="{home_local_bin}:$PATH"')
        logger.warning("ℹ️ После этого выполните: source ~/.bashrc (или перезапустите терминал)")

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
                f"Версия uv: {version}",
                f"PATH настроен: {'да' if path_ok else 'нет'}",
            ],
        )

    def get_info_lines(self) -> tuple[str, ...]:
        """Возвращает краткую информацию о сервисе для интерактивного UI."""
        return self.INFO_LINES

    def install(self) -> bool:
        """Устанавливает uv (идемпотентно: безопасно запускать много раз)"""
        try:
            logger.info("🐍 Начало установки uv (современного менеджера пакетов Python)...")

            logger.debug("🔍 Проверка наличия uv в системе...")
            if self._is_uv_installed():
                version_result = run(self._get_uv_command("--version"), check=False)
                version = version_result.stdout.strip()
                logger.info(f"✅ uv уже установлен: {version} 🎉")
                if not self._is_path_configured():
                    self._warn_about_missing_path()
                return True

            logger.debug("📦 Проверка наличия утилиты curl для загрузки установщика...")
            curl_result = run(["apt", "install", "-y", "curl"], check=False)
            logger.debug(f"📋 apt install curl вывод:\n{curl_result.stdout.strip()}")
            if curl_result.returncode != 0:
                logger.warning("⚠️ curl уже установлен или возникла незначительная ошибка")

            logger.info("⬇️ Запуск официального установщика uv...")
            download_result = run(
                ["curl", "-LsSf", self.UV_INSTALL_URL, "-o", "uv_install.sh"],
                check=False,
            )
            if download_result.returncode != 0:
                logger.error("❌ Не удалось скачать скрипт установки uv")
                return False
            logger.debug("✅ Скрипт загружен")

            logger.debug("🔧 Запуск установки uv в неинтерактивном режиме...")
            install_result = run(
                ["sh", "./uv_install.sh"],
                check=False,
                env={"UV_UNINSTALL": "0"},
            )
            logger.debug(f"📋 uv install вывод:\n{install_result.stdout.strip()}")

            if install_result.returncode != 0:
                logger.error("❌ Ошибка при выполнении скрипта установки uv")
                return False
            logger.debug("✅ Скрипт установки завершён")

            logger.debug("🧹 Очистка временных файлов после установки uv...")
            run(["rm", "-f", "uv_install.sh"], check=False)
            logger.debug("✅ uv_install.sh удалён")

            logger.debug("🔍 Финальная проверка успешной установки uv...")
            if self._is_uv_installed():
                version_result = run(self._get_uv_command("--version"), check=False)
                version = version_result.stdout.strip()
                logger.info(f"✅ uv успешно установлен! {version} 🎉")
                if not self._is_path_configured():
                    self._warn_about_missing_path()
                return True

            logger.error("❌ uv не обнаружен после установки")
            logger.warning("💡 Проверьте, что ~/.local/bin добавлен в PATH текущего пользователя")
            return False

        except FileNotFoundError as e:
            logger.error(f"📁 Команда не найдена: {e}")
            return False
        except PermissionError as e:
            logger.error(f"🔐 Ошибка прав доступа: {e}")
            return False
        except Exception:
            logger.exception("💥 Критическая ошибка при установке uv")
            return False

    def uninstall(self, confirm: bool = False) -> bool:
        """Полностью удаляет uv и его данные (идемпотентно)"""
        try:
            if confirm:
                confirmation = input(
                    "⚠️ Вы уверены, что хотите удалить uv и все его данные? (y/N): "
                )
                if confirmation.lower() not in ["y", "yes"]:
                    logger.info("❌ Удаление uv отменено пользователем")
                    return True

            logger.warning("⚠️ Начало удаления uv (современного менеджера пакетов Python)...")

            logger.debug("🔍 Проверка наличия uv в системе...")
            if not self._is_uv_installed():
                logger.info("✅ uv не установлен, пропускаем удаление 🧹")
                run(
                    ["rm", "-f", str(self.UV_EXECUTABLE), str(self.UVX_EXECUTABLE)],
                    check=False,
                )
                return True

            logger.debug("🧹 Очистка кэша uv (временные файлы и зависимости)...")
            cache_result = run(self._get_uv_command("cache", "clean"), check=False)
            logger.debug(f"📋 uv cache clean вывод:\n{cache_result.stdout.strip()}")
            if cache_result.returncode == 0:
                logger.debug("✅ Кэш очищен")
            else:
                logger.warning("⚠️ Не удалось очистить кэш (возможно, уже пуст)")

            logger.debug("🔍 Получение путей к директориям данных uv...")
            paths = self._get_uv_paths()

            if paths:
                logger.debug(f"🗑️ Удаление директории Python: {paths['python']}...")
                python_result = run(["rm", "-rf", paths["python"]], check=False)
                logger.debug(
                    f"🗑️ Python dir: {'удалено' if python_result.returncode == 0 else 'ошибка'}"
                )

                logger.debug(f"🗑️ Удаление директории инструментов: {paths['tool']}...")
                tool_result = run(["rm", "-rf", paths["tool"]], check=False)
                logger.debug(
                    f"🗑️ Tool dir: {'удалено' if tool_result.returncode == 0 else 'ошибка'}"
                )
            else:
                logger.warning("⚠️ Не удалось получить пути uv, пропускаем удаление директорий")

            logger.debug("🧹 Удаление исполняемых файлов uv и uvx...")
            bin_result = run(
                ["rm", "-f", str(self.UV_EXECUTABLE), str(self.UVX_EXECUTABLE)],
                check=False,
            )
            logger.debug(f"🗑️ Bin files: {'удалено' if bin_result.returncode == 0 else 'ошибка'}")

            if self.ENV_FILE.exists():
                logger.debug("🧹 Очистка env-файла...")
                run(["rm", "-f", str(self.ENV_FILE)], check=False)
                logger.debug(f"✅ Удалён {self.ENV_FILE}")

            logger.debug("🔍 Финальная проверка полного удаления uv из системы...")
            if not self._is_uv_installed():
                logger.info("✅ uv полностью удалён 🧹")
                return True

            logger.warning("⚠️ uv всё ещё обнаружен в системе")
            logger.warning(
                "💡 Попробуйте удалить вручную: rm -rf ~/.local/bin/uv ~/.local/bin/uvx"
            )
            return False

        except FileNotFoundError:
            logger.info("✅ uv уже удалён (команда не найдена) 🧹")
            return True
        except PermissionError as e:
            logger.error(f"🔐 Ошибка прав доступа: {e}")
            return False
        except Exception:
            logger.exception("💥 Критическая ошибка при удалении uv")
            return False
