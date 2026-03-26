import time
from pathlib import Path

from app.utils.logger import get_logger
from app.utils.subprocess_utils import run
from app.utils.update_utils import update_os

logger = get_logger(__name__)


class BBRService:
    # 🔧 Выносим пути в константы класса
    MODULE_CONFIG_PATH = "/etc/modules-load.d/bbr.conf"
    SYSCTL_CONFIG_PATH = "/etc/sysctl.d/10-bbr-fq_codel.conf"

    # 🔧 Выносим конфигурационные строки в константы
    CUBIC = "net.ipv4.tcp_congestion_control=cubic"
    BBR = "net.ipv4.tcp_congestion_control=bbr"
    FQ_CODEL = "net.core.default_qdisc=fq_codel"

    def __init__(self):
        # 🔧 Формируем конфиги из констант
        self.safe_config = f"{self.CUBIC}\n{self.FQ_CODEL}"
        self.bbr_config = f"{self.BBR}\n{self.FQ_CODEL}"

    def _get_current_congestion_control(self) -> str | None:
        """
        Возвращает текущий алгоритм управления перегрузками.
        Returns: 'bbr', 'cubic' или None при ошибке
        """
        try:
            logger.debug("🔍 Проверка текущего алгоритма перегрузок...")
            result = run(["sysctl", "-n", "net.ipv4.tcp_congestion_control"], check=False)
            if result.returncode == 0:
                value = result.stdout.strip()
                logger.debug(f"📡 Текущий алгоритм: {value}")
                return value
            logger.debug(f"❌ sysctl вернул код {result.returncode}")
            return None
        except FileNotFoundError:
            logger.debug("❌ Команда sysctl не найдена")
            return None
        except Exception as e:
            logger.debug(f"❌ Ошибка при получении алгоритма: {e}")
            return None

    def _is_bbr_module_loaded(self) -> bool:
        """Проверяет, загружен ли модуль ядра tcp_bbr"""
        try:
            logger.debug("🔍 Проверка загрузки модуля tcp_bbr через lsmod...")
            result = run(["lsmod"], check=False)
            if result.returncode != 0:
                logger.debug(f"❌ lsmod вернул код {result.returncode}")
                return False
            is_loaded = "tcp_bbr" in result.stdout
            logger.debug(f"📦 Модуль tcp_bbr загружен: {is_loaded}")
            return is_loaded
        except Exception as e:
            logger.warning(f"⚠️ Ошибка при проверке модуля: {e}")
            return False

    def _write_config_file(self, path: str, content: str, description: str) -> bool:
        """
        Универсальный метод для записи конфигурационных файлов.
        Returns: True при успехе, False при ошибке
        """
        try:
            logger.debug(f"📝 Запись {description} в {path}...")
            config_path = Path(path)
            config_path.parent.mkdir(parents=True, exist_ok=True)  # Создаём директорию если нужно

            with open(config_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.debug(f"✅ Записано в {path}")
            return True
        except PermissionError:
            logger.error(f"🔐 Нет прав для записи в {path} (требуется root?)")
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка записи в {path}: {e}")
            return False

    def enable_bbr(self) -> None:
        """Включает BBR (идемпотентно: безопасно запускать много раз)"""
        try:
            logger.info("🚀 Начало включения TCP BBR Congestion Control...")

            # 🔍 Проверка: а может, BBR уже включен?
            logger.info("🔍 Проверка текущего состояния алгоритма управления перегрузками...")
            current_algo = self._get_current_congestion_control()
            if current_algo == "bbr":
                logger.info("✅ BBR уже включен 🎉")
                return
            elif current_algo:
                logger.info(f"ℹ️ Текущий алгоритм: {current_algo}, переключаем на bbr...")
            else:
                logger.warning("⚠️ Не удалось определить текущий алгоритм, продолжаем...")

            # 🔄 Обновление системы
            logger.info("🔄 Обновление системы перед включением BBR...")
            update_os()
            logger.debug("✅ Система обновлена")

            # 📦 Шаг 1: Загрузка модуля ядра
            if not self._is_bbr_module_loaded():
                logger.info("📦 Модуль ядра tcp_bbr не загружен, выполняем загрузку...")
                modprobe_result = run(["modprobe", "tcp_bbr"], check=False)
                logger.debug(f"🔧 modprobe вывод: {modprobe_result.stdout.strip()}")

                if modprobe_result.returncode != 0:
                    logger.error("❌ Не удалось загрузить модуль tcp_bbr (modprobe failed)")
                    return

                time.sleep(0.5)  # Даём ядру время на загрузку модуля

                if not self._is_bbr_module_loaded():
                    logger.error("❌ Модуль tcp_bbr не загрузился после modprobe")
                    return
                logger.debug("✅ Модуль tcp_bbr успешно загружен")
            else:
                logger.debug("✅ Модуль tcp_bbr уже загружен")

            # 📝 Шаг 2: Конфиг автозагрузки модуля
            if not self._write_config_file(
                self.MODULE_CONFIG_PATH, "tcp_bbr\n", "автозагрузка модуля"
            ):
                return
            logger.debug(f"✅ Конфиг модуля: {self.MODULE_CONFIG_PATH}")

            # ⚙️ Шаг 3: Конфиг sysctl
            if not self._write_config_file(
                self.SYSCTL_CONFIG_PATH, self.bbr_config, "параметры sysctl для BBR"
            ):
                return
            logger.debug(f"✅ Конфиг sysctl: {self.SYSCTL_CONFIG_PATH}")

            # 🔄 Шаг 4: Применение настроек
            logger.info("🔄 Применение настроек sysctl для BBR...")
            start_time = time.time()
            sysctl_result = run(["sysctl", "--system"], check=False)
            elapsed = time.time() - start_time

            logger.debug(f"⏱️ sysctl --system выполнен за {elapsed:.2f}s")
            if sysctl_result.returncode != 0:
                logger.warning(f"⚠️ sysctl --system вернул код {sysctl_result.returncode}")
            logger.debug(f"📋 Вывод sysctl: {sysctl_result.stdout.strip()}")

            # ✅ Шаг 5: Финальная проверка
            logger.info("🔍 Финальная проверка...")
            final_algo = self._get_current_congestion_control()

            if final_algo == "bbr":
                logger.info("✅ TCP BBR Congestion Control успешно включен (алгоритм: bbr) 🎉")
            elif final_algo:
                logger.error(f"❌ Ожидалось 'bbr', но активно: '{final_algo}'")
            else:
                logger.error("❌ Не удалось проверить текущий алгоритм после применения настроек")

        except FileNotFoundError as e:
            logger.error(f"📁 Команда не найдена: {e}")
        except PermissionError as e:
            logger.error(f"🔐 Ошибка прав доступа (требуется root?): {e}")
        except Exception:
            logger.exception("💥 Критическая ошибка при включении BBR")

    def disable_bbr(self, confirm: bool = False) -> None:
        """Отключает BBR и возвращает cubic (идемпотентно)"""
        if confirm:
            confirmation = input(
                "⚠️ Вы уверены, что хотите отключить TCP BBR Congestion Control? (y/N): "
            )
            if confirmation.lower() not in ["y", "yes"]:
                print("❌ Отключение BBR отменено пользователем")
                return
        try:
            logger.info("🔻 Начало отключения TCP BBR Congestion Control...")

            # 🔍 Проверка: а может, BBR уже выключен?
            logger.info("🔍 Проверка текущего состояния алгоритма управления перегрузками...")
            current_algo = self._get_current_congestion_control()
            if current_algo == "cubic":
                logger.info("✅ Уже используется cubic, ничего не делаем 🎯")
                return
            elif current_algo == "bbr":
                logger.info("ℹ️ Обнаружен BBR, переключаем на cubic...")
            elif current_algo:
                logger.info(f"ℹ️ Текущий алгоритм: {current_algo}, переключаем на cubic...")
            else:
                logger.warning("⚠️ Не удалось определить текущий алгоритм, продолжаем...")

            # ♻️ Шаг 1: Восстановление конфига sysctl
            logger.info(
                "♻️ Восстановление настроек по умолчанию для алгоритма управления перегрузками..."
            )
            if not self._write_config_file(
                self.SYSCTL_CONFIG_PATH, self.safe_config, "параметры sysctl по умолчанию"
            ):
                return
            logger.debug(f"✅ Восстановлен конфиг: {self.SYSCTL_CONFIG_PATH}")

            # 🔄 Шаг 2: Применение настроек (с индивидуальными параметрами для надёжности)
            logger.info("🔄 Применение настроек sysctl...")

            cc_result = run(["sysctl", "-w", self.CUBIC], check=False)
            logger.debug(f"⚙️ congestion_control: {cc_result.stdout.strip()}")
            if cc_result.returncode != 0:
                logger.warning("⚠️ Не удалось применить net.ipv4.tcp_congestion_control=cubic")

            qdisc_result = run(["sysctl", "-w", self.FQ_CODEL], check=False)
            logger.debug(f"⚙️ qdisc: {qdisc_result.stdout.strip()}")
            if qdisc_result.returncode != 0:
                logger.warning("⚠️ Не удалось применить net.core.default_qdisc=fq_codel")

            # ✅ Шаг 3: Финальная проверка
            logger.info("🔍 Финальная проверка...")
            final_algo = self._get_current_congestion_control()

            if final_algo == "cubic":
                logger.info(
                    "✅ TCP BBR Congestion Control выключен, восстановлен алгоритм cubic 🎯"
                )
            elif final_algo == "bbr":
                logger.error("❌ BBR всё ещё активен после отключения")
            elif final_algo:
                logger.warning(f"⚠️ Установлен алгоритм '{final_algo}' (ожидалось 'cubic')")
            else:
                logger.warning("⚠️ Не удалось проверить текущий алгоритм после отключения")

        except FileNotFoundError as e:
            logger.error(f"📁 Команда не найдена: {e}")
        except PermissionError as e:
            logger.error(f"🔐 Ошибка прав доступа (требуется root?): {e}")
        except Exception:
            logger.exception("💥 Критическая ошибка при отключении BBR")
