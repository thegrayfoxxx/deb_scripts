from pathlib import Path

from app.utils.logger import get_logger
from app.utils.subprocess_utils import run

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

    def _is_uv_installed(self) -> bool:
        """Проверяет, установлен ли uv в системе"""
        try:
            logger.debug("🔍 Проверка наличия uv...")
            result = run(self.UV_VERSION_CMD, check=False)
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

            python_result = run(self.UV_PYTHON_DIR_CMD, check=False)
            tool_result = run(self.UV_TOOL_DIR_CMD, check=False)

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

    def _add_to_path_if_needed(self) -> bool:
        """
        Проверяет, есть ли ~/.local/bin в PATH, и предупреждает если нет.
        Returns: True если путь уже в PATH или добавлен успешно
        """
        import os

        home_local_bin = str(Path.home() / ".local" / "bin")
        current_path = os.environ.get("PATH", "")

        if home_local_bin in current_path:
            logger.debug("✅ ~/.local/bin уже в PATH")
            return True

        logger.warning("⚠️ ~/.local/bin не в PATH. Добавьте в ~/.bashrc или ~/.zshrc:")
        logger.warning(f'   export PATH="{home_local_bin}:$PATH"')
        logger.warning("ℹ️ После этого выполните: source ~/.bashrc (или перезапустите терминал)")
        return False

    def install(self) -> bool:
        """Единая точка входа для установки uv."""
        return self.install_uv()

    def uninstall(self, confirm: bool = False) -> bool:
        """Единая точка входа для удаления uv."""
        return self.uninstall_uv(confirm=confirm)

    def is_installed(self) -> bool:
        """Проверяет, установлен ли uv."""
        return self._is_uv_installed()

    def get_status(self) -> str:
        """Возвращает человекочитаемый статус uv."""
        if not self._is_uv_installed():
            return "uv: not installed"

        version_result = run(self.UV_VERSION_CMD, check=False)
        version = version_result.stdout.strip() if version_result.returncode == 0 else "unknown"
        path_ok = self._add_to_path_if_needed()
        return (
            "uv: installed\n"
            f"Version: {version}\n"
            f"PATH configured: {'yes' if path_ok else 'no'}"
        )

    def install_uv(self) -> bool:
        """Устанавливает uv (идемпотентно: безопасно запускать много раз)"""
        try:
            logger.info("🐍 Начало установки uv (современного менеджера пакетов Python)...")

            # 🔍 Проверка: а может, uv уже установлен?
            logger.info("🔍 Проверка наличия uv в системе...")
            if self._is_uv_installed():
                version_result = run(self.UV_VERSION_CMD, check=False)
                version = version_result.stdout.strip()
                logger.info(f"✅ uv уже установлен: {version} 🎉")
                self._add_to_path_if_needed()
                return True

            # 📦 Шаг 1: Установка curl (если нет)
            logger.info("📦 Проверка наличия утилиты curl для загрузки установщика...")
            curl_result = run(["apt", "install", "-y", "curl"], check=False)
            logger.debug(f"📋 apt install curl вывод:\n{curl_result.stdout.strip()}")
            if curl_result.returncode != 0:
                logger.warning("⚠️ curl уже установлен или возникла незначительная ошибка")

            # ⬇️ Шаг 2: Скачивание скрипта установки
            logger.info("⬇️ Скачивание официального скрипта установки uv с astral.sh...")
            download_result = run(
                ["curl", "-LsSf", self.UV_INSTALL_URL, "-o", "uv_install.sh"], check=False
            )
            if download_result.returncode != 0:
                logger.error("❌ Не удалось скачать скрипт установки uv")
                return False
            logger.debug("✅ Скрипт загружен")

            # 🔧 Шаг 3: Запуск установки
            logger.info("🔧 Запуск установки uv в неинтерактивном режиме...")
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

            # 🧹 Шаг 4: Очистка временных файлов
            logger.info("🧹 Очистка временных файлов после установки uv...")
            run(["rm", "-f", "uv_install.sh"], check=False)
            logger.debug("✅ uv_install.sh удалён")

            # ✅ Шаг 5: Финальная проверка установки
            logger.info("🔍 Финальная проверка успешной установки uv...")
            if self._is_uv_installed():
                version_result = run(self.UV_VERSION_CMD, check=False)
                version = version_result.stdout.strip()
                logger.info(f"✅ uv успешно установлен! {version} 🎉")
                self._add_to_path_if_needed()
                return True

            logger.error("❌ uv не обнаружен после установки")
            logger.warning("💡 Попробуйте выполнить: source ~/.local/bin/env")
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

    def uninstall_uv(self, confirm: bool = False) -> bool:
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

            # 🔍 Проверка: а установлен ли uv вообще?
            logger.info("🔍 Проверка наличия uv в системе...")
            if not self._is_uv_installed():
                logger.info("✅ uv не установлен, пропускаем удаление 🧹")
                run(["rm", "-f", str(self.UV_EXECUTABLE), str(self.UVX_EXECUTABLE)], check=False)
                return True

            # 🗑️ Шаг 1: Очистка кэша
            logger.info("🧹 Очистка кэша uv (временные файлы и зависимости)...")
            cache_result = run(self.UV_CACHE_CLEAN_CMD, check=False)
            logger.debug(f"📋 uv cache clean вывод:\n{cache_result.stdout.strip()}")
            if cache_result.returncode == 0:
                logger.debug("✅ Кэш очищен")
            else:
                logger.warning("⚠️ Не удалось очистить кэш (возможно, уже пуст)")

            # 📁 Шаг 2: Получение путей к данным
            logger.info("🔍 Получение путей к директориям данных uv...")
            paths = self._get_uv_paths()

            if paths:
                logger.info(f"🗑️ Удаление директории Python: {paths['python']}...")
                python_result = run(["rm", "-rf", paths["python"]], check=False)
                logger.debug(
                    f"🗑️ Python dir: {'удалено' if python_result.returncode == 0 else 'ошибка'}"
                )

                logger.info(f"🗑️ Удаление директории инструментов: {paths['tool']}...")
                tool_result = run(["rm", "-rf", paths["tool"]], check=False)
                logger.debug(
                    f"🗑️ Tool dir: {'удалено' if tool_result.returncode == 0 else 'ошибка'}"
                )
            else:
                logger.warning("⚠️ Не удалось получить пути uv, пропускаем удаление директорий")

            # 🧹 Шаг 3: Удаление исполняемых файлов
            logger.info("🧹 Удаление исполняемых файлов uv и uvx...")
            bin_result = run(
                ["rm", "-f", str(self.UV_EXECUTABLE), str(self.UVX_EXECUTABLE)], check=False
            )
            logger.debug(f"🗑️ Bin files: {'удалено' if bin_result.returncode == 0 else 'ошибка'}")

            # ♻️ Шаг 4: Очистка env-файла (опционально)
            if self.ENV_FILE.exists():
                logger.info("🧹 Очистка env-файла...")
                run(["rm", "-f", str(self.ENV_FILE)], check=False)
                logger.debug(f"✅ Удалён {self.ENV_FILE}")

            # 🔍 Шаг 5: Финальная проверка
            logger.info("🔍 Финальная проверка полного удаления uv из системы...")
            if not self._is_uv_installed():
                logger.info("✅ uv полностью удалён 🧹")
                return True

            logger.warning("⚠️ uv всё ещё обнаружен в системе")
            logger.warning("💡 Попробуйте удалить вручную: rm -rf ~/.local/bin/uv ~/.local/bin/uvx")
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
