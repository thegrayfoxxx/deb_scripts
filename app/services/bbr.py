import time
from pathlib import Path

from app.bootstrap.logger import get_logger
from app.core.status import format_status_snapshot
from app.core.subprocess import run

logger = get_logger(__name__)


class BBRService:
    # 🔧 Выносим пути в константы класса
    MODULE_CONFIG_PATH = "/etc/modules-load.d/bbr.conf"
    SYSCTL_CONFIG_PATH = "/etc/sysctl.d/10-bbr-fq_codel.conf"
    INFO_LINES = (
        "BBR (Bottleneck Bandwidth and RTT) — это алгоритм управления перегрузками в TCP",
        "Разработан Google для улучшения производительности сетевых соединений",
        "Основные преимущества:",
        "• Увеличение пропускной способности канала",
        "• Снижение задержек (latency)",
        "• Лучшая стабильность при высокой нагрузке",
        "• Оптимизация для VPS и выделенных серверов",
        "🔗 GitHub репозиторий: https://github.com/google/bbr",
    )

    # 🔧 Выносим конфигурационные строки в константы
    CUBIC = "net.ipv4.tcp_congestion_control=cubic"
    BBR = "net.ipv4.tcp_congestion_control=bbr"
    FQ_CODEL = "net.core.default_qdisc=fq_codel"

    def __init__(self):
        # 🔧 Формируем конфиги из констант
        self.safe_config = f"{self.CUBIC}\n{self.FQ_CODEL}"
        self.bbr_config = f"{self.BBR}\n{self.FQ_CODEL}"

    def is_installed(self) -> bool:
        """Возвращает True, если конфигурация BBR записана в системе."""
        return self._has_bbr_configuration()

    def is_active(self) -> bool:
        """Возвращает True, если BBR сейчас активен."""
        return self._get_current_congestion_control() == "bbr"

    def get_info_lines(self) -> tuple[str, ...]:
        """Возвращает краткую информацию о сервисе для интерактивного UI."""
        return self.INFO_LINES

    def get_status(self) -> str:
        """Возвращает человекочитаемый статус BBR."""
        installed = self.is_installed()
        current_algo = self._get_current_congestion_control()
        module_loaded = self._is_bbr_module_loaded()
        details = []

        if current_algo:
            details.append(f"Текущий алгоритм перегрузки: {current_algo}")
        else:
            details.append("Текущий алгоритм перегрузки: недоступен")

        details.append(f"Модуль tcp_bbr: {'загружен' if module_loaded else 'не загружен'}")

        return format_status_snapshot(
            installed=installed,
            active=current_algo == "bbr",
            details=details,
        )

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

    def _has_bbr_configuration(self) -> bool:
        """Проверяет наличие конфигурации BBR в файловой системе."""
        try:
            module_config = Path(self.MODULE_CONFIG_PATH)
            sysctl_config = Path(self.SYSCTL_CONFIG_PATH)

            if not module_config.exists() or not sysctl_config.exists():
                return False

            module_content = module_config.read_text(encoding="utf-8", errors="ignore")
            sysctl_content = sysctl_config.read_text(encoding="utf-8", errors="ignore")
            return "tcp_bbr" in module_content and self.BBR in sysctl_content
        except Exception as e:
            logger.debug(f"❌ Ошибка при проверке конфигурации BBR: {e}")
            return False

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

    def install(self) -> bool:
        """Подготавливает BBR: модуль автозагрузки и sysctl-конфигурацию."""
        try:
            logger.info("📦 Подготовка конфигурации TCP BBR...")

            if self._has_bbr_configuration():
                logger.info("✅ Конфигурация BBR уже подготовлена 🎉")
                return True

            if not self._is_bbr_module_loaded():
                logger.debug("📦 Модуль tcp_bbr не загружен, выполняем modprobe...")
                modprobe_result = run(["modprobe", "tcp_bbr"], check=False)
                if modprobe_result.returncode != 0:
                    logger.error("❌ Не удалось загрузить модуль tcp_bbr (modprobe failed)")
                    return False

            if not self._write_config_file(
                self.MODULE_CONFIG_PATH, "tcp_bbr\n", "автозагрузка модуля"
            ):
                return False

            if not self._write_config_file(
                self.SYSCTL_CONFIG_PATH, self.bbr_config, "параметры sysctl для BBR"
            ):
                return False

            if self._has_bbr_configuration():
                logger.info("✅ Конфигурация BBR успешно подготовлена")
                return True

            logger.error("❌ Конфигурация BBR не обнаружена после подготовки")
            return False
        except FileNotFoundError as e:
            logger.error(f"📁 Команда не найдена: {e}")
            return False
        except PermissionError as e:
            logger.error(f"🔐 Ошибка прав доступа (требуется root?): {e}")
            return False
        except Exception:
            logger.exception("💥 Критическая ошибка при подготовке BBR")
            return False

    def uninstall(self, confirm: bool = False) -> bool:
        """Удаляет конфигурацию BBR и возвращает безопасный алгоритм по умолчанию."""
        if not self.deactivate(confirm=confirm):
            return False

        try:
            logger.warning("⚠️ Удаление конфигурации TCP BBR...")
            run(["rm", "-f", self.MODULE_CONFIG_PATH], check=False)
            run(["rm", "-f", self.SYSCTL_CONFIG_PATH], check=False)

            if (
                not Path(self.MODULE_CONFIG_PATH).exists()
                and not Path(self.SYSCTL_CONFIG_PATH).exists()
            ):
                logger.info("✅ Конфигурация BBR удалена 🧹")
                return True

            logger.warning("⚠️ Конфигурация BBR частично осталась в системе")
            return False
        except Exception:
            logger.exception("💥 Критическая ошибка при удалении конфигурации BBR")
            return False

    def activate(self) -> bool:
        """Включает BBR (идемпотентно: безопасно запускать много раз)"""
        try:
            logger.info("🚀 Начало включения TCP BBR Congestion Control...")

            if not self.install():
                return False

            logger.debug("🔍 Проверка текущего состояния алгоритма управления перегрузками...")
            current_algo = self._get_current_congestion_control()
            if current_algo == "bbr":
                logger.info("✅ BBR уже включен 🎉")
                return True
            if current_algo:
                logger.debug(f"ℹ️ Текущий алгоритм: {current_algo}, переключаем на bbr...")
            else:
                logger.warning("⚠️ Не удалось определить текущий алгоритм, продолжаем...")

            if not self._is_bbr_module_loaded():
                logger.debug("📦 Модуль ядра tcp_bbr не загружен, выполняем загрузку...")
                modprobe_result = run(["modprobe", "tcp_bbr"], check=False)
                logger.debug(f"🔧 modprobe вывод: {modprobe_result.stdout.strip()}")

                if modprobe_result.returncode != 0:
                    logger.error("❌ Не удалось загрузить модуль tcp_bbr (modprobe failed)")
                    return False

                time.sleep(0.5)  # Даём ядру время на загрузку модуля

                if not self._is_bbr_module_loaded():
                    logger.error("❌ Модуль tcp_bbr не загрузился после modprobe")
                    return False
                logger.debug("✅ Модуль tcp_bbr успешно загружен")
            else:
                logger.debug("✅ Модуль tcp_bbr уже загружен")

            logger.debug("🔄 Применение настроек sysctl для BBR...")
            start_time = time.time()
            sysctl_result = run(["sysctl", "--system"], check=False)
            elapsed = time.time() - start_time

            logger.debug(f"⏱️ sysctl --system выполнен за {elapsed:.2f}s")
            if sysctl_result.returncode != 0:
                logger.warning(
                    "⚠️ sysctl --system завершился с предупреждением, перепроверяю результат"
                )
            logger.debug(f"📋 Вывод sysctl: {sysctl_result.stdout.strip()}")

            logger.debug("🔍 Финальная проверка...")
            final_algo = self._get_current_congestion_control()

            if final_algo == "bbr":
                logger.info("✅ TCP BBR Congestion Control успешно включен (алгоритм: bbr) 🎉")
                return True
            if final_algo:
                logger.error(f"❌ Ожидалось 'bbr', но активно: '{final_algo}'")
                return False

            logger.error("❌ Не удалось проверить текущий алгоритм после применения настроек")
            return False

        except FileNotFoundError as e:
            logger.error(f"📁 Команда не найдена: {e}")
            return False
        except PermissionError as e:
            logger.error(f"🔐 Ошибка прав доступа (требуется root?): {e}")
            return False
        except Exception:
            logger.exception("💥 Критическая ошибка при включении BBR")
            return False

    def deactivate(self, confirm: bool = False) -> bool:
        """Отключает BBR и возвращает cubic (идемпотентно)"""
        if confirm:
            confirmation = input(
                "⚠️ Вы уверены, что хотите отключить TCP BBR Congestion Control? (y/N): "
            )
            if confirmation.lower() not in ["y", "yes"]:
                logger.info("❌ Отключение BBR отменено пользователем")
                return True
        try:
            logger.info("🔻 Начало отключения TCP BBR Congestion Control...")

            logger.debug("🔍 Проверка текущего состояния алгоритма управления перегрузками...")
            current_algo = self._get_current_congestion_control()
            if current_algo == "cubic":
                logger.info("✅ Уже используется cubic, ничего не делаем 🎯")
                return True
            if current_algo == "bbr":
                logger.debug("ℹ️ Обнаружен BBR, переключаем на cubic...")
            elif current_algo:
                logger.debug(f"ℹ️ Текущий алгоритм: {current_algo}, переключаем на cubic...")
            else:
                logger.warning("⚠️ Не удалось определить текущий алгоритм, продолжаем...")

            logger.debug(
                "♻️ Восстановление настроек по умолчанию для алгоритма управления перегрузками..."
            )
            if not self._write_config_file(
                self.SYSCTL_CONFIG_PATH,
                self.safe_config,
                "параметры sysctl по умолчанию",
            ):
                return False
            logger.debug(f"✅ Восстановлен конфиг: {self.SYSCTL_CONFIG_PATH}")

            logger.debug("🔄 Применение настроек sysctl...")

            cc_result = run(["sysctl", "-w", self.CUBIC], check=False)
            logger.debug(f"⚙️ congestion_control: {cc_result.stdout.strip()}")
            if cc_result.returncode != 0:
                logger.warning("⚠️ Не удалось применить net.ipv4.tcp_congestion_control=cubic")

            qdisc_result = run(["sysctl", "-w", self.FQ_CODEL], check=False)
            logger.debug(f"⚙️ qdisc: {qdisc_result.stdout.strip()}")
            if qdisc_result.returncode != 0:
                logger.warning("⚠️ Не удалось применить net.core.default_qdisc=fq_codel")

            logger.debug("🔍 Финальная проверка...")
            final_algo = self._get_current_congestion_control()

            if final_algo == "cubic":
                logger.info(
                    "✅ TCP BBR Congestion Control выключен, восстановлен алгоритм cubic 🎯"
                )
                return True
            if final_algo == "bbr":
                logger.error("❌ BBR всё ещё активен после отключения")
                return False
            if final_algo:
                logger.warning(f"⚠️ Установлен алгоритм '{final_algo}' (ожидалось 'cubic')")
                return False

            logger.warning("⚠️ Не удалось проверить текущий алгоритм после отключения")
            return False

        except FileNotFoundError as e:
            logger.error(f"📁 Команда не найдена: {e}")
            return False
        except PermissionError as e:
            logger.error(f"🔐 Ошибка прав доступа (требуется root?): {e}")
            return False
        except Exception:
            logger.exception("💥 Критическая ошибка при отключении BBR")
            return False
