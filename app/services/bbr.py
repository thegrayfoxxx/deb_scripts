import time
from pathlib import Path

from app.bootstrap.logger import get_logger
from app.core.status import format_status_snapshot
from app.core.subprocess import run
from app.i18n.locale import is_affirmative_reply, t, tr

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

    def is_installed(self) -> bool:
        """Возвращает True, если конфигурация BBR записана в системе."""
        return self._has_bbr_configuration()

    def is_active(self) -> bool:
        """Возвращает True, если BBR сейчас активен."""
        return self._get_current_congestion_control() == "bbr"

    def get_info_lines(self) -> tuple[str, ...]:
        """Возвращает краткую информацию о сервисе для интерактивного UI."""
        return (
            t("info.bbr.line1"),
            t("info.bbr.line2"),
            t("info.bbr.line3"),
            t("info.bbr.line4"),
            t("info.bbr.line5"),
            t("info.bbr.line6"),
            t("info.bbr.line7"),
            t("info.bbr.line8"),
        )

    def get_status(self) -> str:
        """Возвращает человекочитаемый статус BBR."""
        installed = self.is_installed()
        current_algo = self._get_current_congestion_control()
        module_loaded = self._is_bbr_module_loaded()
        details = []

        if current_algo:
            details.append(t("status.current_congestion_algorithm", value=current_algo))
        else:
            details.append(t("status.current_congestion_algorithm", value=t("status.unavailable")))

        details.append(
            t("status.kernel_module_loaded")
            if module_loaded
            else t("status.kernel_module_not_loaded")
        )

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
            logger.debug(
                tr(
                    "🔍 Проверка текущего алгоритма перегрузок...",
                    "🔍 Checking the current congestion-control algorithm...",
                )
            )
            result = run(["sysctl", "-n", "net.ipv4.tcp_congestion_control"], check=False)
            if result.returncode == 0:
                value = result.stdout.strip()
                logger.debug(tr(f"📡 Текущий алгоритм: {value}", f"📡 Current algorithm: {value}"))
                return value
            logger.debug(
                tr(
                    f"❌ sysctl вернул код {result.returncode}",
                    f"❌ sysctl returned code {result.returncode}",
                )
            )
            return None
        except FileNotFoundError:
            logger.debug(tr("❌ Команда sysctl не найдена", "❌ sysctl command not found"))
            return None
        except Exception as e:
            logger.debug(
                tr(
                    f"❌ Ошибка при получении алгоритма: {e}",
                    f"❌ Error while retrieving algorithm: {e}",
                )
            )
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
            logger.debug(
                tr(
                    f"❌ Ошибка при проверке конфигурации BBR: {e}",
                    f"❌ Error while checking BBR configuration: {e}",
                )
            )
            return False

    def _is_bbr_module_loaded(self) -> bool:
        """Проверяет, загружен ли модуль ядра tcp_bbr"""
        try:
            logger.debug(
                tr(
                    "🔍 Проверка загрузки модуля tcp_bbr через lsmod...",
                    "🔍 Checking whether the tcp_bbr module is loaded via lsmod...",
                )
            )
            result = run(["lsmod"], check=False)
            if result.returncode != 0:
                logger.debug(
                    tr(
                        f"❌ lsmod вернул код {result.returncode}",
                        f"❌ lsmod returned code {result.returncode}",
                    )
                )
                return False
            is_loaded = "tcp_bbr" in result.stdout
            logger.debug(
                tr(
                    f"📦 Модуль tcp_bbr загружен: {is_loaded}",
                    f"📦 tcp_bbr module loaded: {is_loaded}",
                )
            )
            return is_loaded
        except Exception as e:
            logger.warning(
                tr(f"⚠️ Ошибка при проверке модуля: {e}", f"⚠️ Error while checking the module: {e}")
            )
            return False

    def _write_config_file(self, path: str, content: str, description: str) -> bool:
        """
        Универсальный метод для записи конфигурационных файлов.
        Returns: True при успехе, False при ошибке
        """
        try:
            logger.debug(
                tr(
                    f"📝 Запись {description} в {path}...",
                    f"📝 Writing {description} to {path}...",
                )
            )
            config_path = Path(path)
            config_path.parent.mkdir(parents=True, exist_ok=True)  # Создаём директорию если нужно

            with open(config_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.debug(tr(f"✅ Записано в {path}", f"✅ Written to {path}"))
            return True
        except PermissionError:
            logger.error(
                tr(
                    f"🔐 Нет прав для записи в {path} (требуется root?)",
                    f"🔐 No permission to write to {path} (is root required?)",
                )
            )
            return False
        except Exception as e:
            logger.error(tr(f"❌ Ошибка записи в {path}: {e}", f"❌ Error writing to {path}: {e}"))
            return False

    def install(self) -> bool:
        """Подготавливает BBR: модуль автозагрузки и sysctl-конфигурацию."""
        try:
            logger.info(
                tr(
                    "📦 Подготовка конфигурации TCP BBR...",
                    "📦 Preparing TCP BBR configuration...",
                )
            )

            if self._has_bbr_configuration():
                logger.info(
                    tr(
                        "✅ Конфигурация BBR уже подготовлена 🎉",
                        "✅ BBR configuration is already prepared 🎉",
                    )
                )
                return True

            if not self._is_bbr_module_loaded():
                logger.debug(
                    tr(
                        "📦 Модуль tcp_bbr не загружен, выполняем modprobe...",
                        "📦 tcp_bbr module is not loaded, running modprobe...",
                    )
                )
                modprobe_result = run(["modprobe", "tcp_bbr"], check=False)
                if modprobe_result.returncode != 0:
                    logger.error(
                        tr(
                            "❌ Не удалось загрузить модуль tcp_bbr (modprobe failed)",
                            "❌ Failed to load the tcp_bbr module (modprobe failed)",
                        )
                    )
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
                logger.info(
                    tr(
                        "✅ Конфигурация BBR успешно подготовлена",
                        "✅ BBR configuration prepared successfully",
                    )
                )
                return True

            logger.error(
                tr(
                    "❌ Конфигурация BBR не обнаружена после подготовки",
                    "❌ BBR configuration was not detected after preparation",
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
                    "💥 Критическая ошибка при подготовке BBR",
                    "💥 Critical error while preparing BBR",
                )
            )
            return False

    def uninstall(self, confirm: bool = False) -> bool:
        """Удаляет конфигурацию BBR и возвращает безопасный алгоритм по умолчанию."""
        if not self.deactivate(confirm=confirm):
            return False

        try:
            logger.warning(
                tr("⚠️ Удаление конфигурации TCP BBR...", "⚠️ Removing TCP BBR configuration...")
            )
            run(["rm", "-f", self.MODULE_CONFIG_PATH], check=False)
            run(["rm", "-f", self.SYSCTL_CONFIG_PATH], check=False)

            if (
                not Path(self.MODULE_CONFIG_PATH).exists()
                and not Path(self.SYSCTL_CONFIG_PATH).exists()
            ):
                logger.info(
                    tr("✅ Конфигурация BBR удалена 🧹", "✅ BBR configuration removed 🧹")
                )
                return True

            logger.warning(
                tr(
                    "⚠️ Конфигурация BBR частично осталась в системе",
                    "⚠️ BBR configuration partially remains on the system",
                )
            )
            return False
        except Exception:
            logger.exception(
                tr(
                    "💥 Критическая ошибка при удалении конфигурации BBR",
                    "💥 Critical error while removing BBR configuration",
                )
            )
            return False

    def activate(self) -> bool:
        """Включает BBR (идемпотентно: безопасно запускать много раз)"""
        try:
            logger.info(
                tr(
                    "🚀 Начало включения TCP BBR Congestion Control...",
                    "🚀 Starting TCP BBR Congestion Control activation...",
                )
            )

            if not self.install():
                return False

            logger.debug(
                tr(
                    "🔍 Проверка текущего состояния алгоритма управления перегрузками...",
                    "🔍 Checking the current congestion-control state...",
                )
            )
            current_algo = self._get_current_congestion_control()
            if current_algo == "bbr":
                logger.info(tr("✅ BBR уже включен 🎉", "✅ BBR is already enabled 🎉"))
                return True
            if current_algo:
                logger.debug(
                    tr(
                        f"ℹ️ Текущий алгоритм: {current_algo}, переключаем на bbr...",
                        f"ℹ️ Current algorithm: {current_algo}, switching to bbr...",
                    )
                )
            else:
                logger.warning(
                    tr(
                        "⚠️ Не удалось определить текущий алгоритм, продолжаем...",
                        "⚠️ Failed to detect the current algorithm, continuing...",
                    )
                )

            if not self._is_bbr_module_loaded():
                logger.debug(
                    tr(
                        "📦 Модуль ядра tcp_bbr не загружен, выполняем загрузку...",
                        "📦 tcp_bbr kernel module is not loaded, loading it...",
                    )
                )
                modprobe_result = run(["modprobe", "tcp_bbr"], check=False)
                logger.debug(
                    tr(
                        f"🔧 modprobe вывод: {modprobe_result.stdout.strip()}",
                        f"🔧 modprobe output: {modprobe_result.stdout.strip()}",
                    )
                )

                if modprobe_result.returncode != 0:
                    logger.error(
                        tr(
                            "❌ Не удалось загрузить модуль tcp_bbr (modprobe failed)",
                            "❌ Failed to load the tcp_bbr module (modprobe failed)",
                        )
                    )
                    return False

                time.sleep(0.5)  # Даём ядру время на загрузку модуля

                if not self._is_bbr_module_loaded():
                    logger.error(
                        tr(
                            "❌ Модуль tcp_bbr не загрузился после modprobe",
                            "❌ The tcp_bbr module did not load after modprobe",
                        )
                    )
                    return False
                logger.debug(
                    tr(
                        "✅ Модуль tcp_bbr успешно загружен",
                        "✅ tcp_bbr module loaded successfully",
                    )
                )
            else:
                logger.debug(
                    tr("✅ Модуль tcp_bbr уже загружен", "✅ tcp_bbr module is already loaded")
                )

            logger.debug(
                tr(
                    "🔄 Применение настроек sysctl для BBR...",
                    "🔄 Applying sysctl settings for BBR...",
                )
            )
            start_time = time.time()
            sysctl_result = run(["sysctl", "--system"], check=False)
            elapsed = time.time() - start_time

            logger.debug(
                tr(
                    f"⏱️ sysctl --system выполнен за {elapsed:.2f}s",
                    f"⏱️ sysctl --system finished in {elapsed:.2f}s",
                )
            )
            if sysctl_result.returncode != 0:
                logger.warning(
                    tr(
                        "⚠️ sysctl --system завершился с предупреждением, перепроверяю результат",
                        "⚠️ sysctl --system finished with a warning, rechecking the result",
                    )
                )
            logger.debug(
                tr(
                    f"📋 Вывод sysctl: {sysctl_result.stdout.strip()}",
                    f"📋 sysctl output: {sysctl_result.stdout.strip()}",
                )
            )

            logger.debug(tr("🔍 Финальная проверка...", "🔍 Final verification..."))
            final_algo = self._get_current_congestion_control()

            if final_algo == "bbr":
                logger.info(
                    tr(
                        "✅ TCP BBR Congestion Control успешно включен (алгоритм: bbr) 🎉",
                        "✅ TCP BBR Congestion Control enabled successfully (algorithm: bbr) 🎉",
                    )
                )
                return True
            if final_algo:
                logger.error(
                    tr(
                        f"❌ Ожидалось 'bbr', но активно: '{final_algo}'",
                        f"❌ Expected 'bbr', but active algorithm is '{final_algo}'",
                    )
                )
                return False

            logger.error(
                tr(
                    "❌ Не удалось проверить текущий алгоритм после применения настроек",
                    "❌ Failed to verify the current algorithm after applying settings",
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
                    "💥 Критическая ошибка при включении BBR",
                    "💥 Critical error while enabling BBR",
                )
            )
            return False

    def deactivate(self, confirm: bool = False) -> bool:
        """Отключает BBR и возвращает cubic (идемпотентно)"""
        if confirm:
            confirmation = input(
                tr(
                    "⚠️ Вы уверены, что хотите отключить TCP BBR Congestion Control? ",
                    "⚠️ Are you sure you want to disable TCP BBR Congestion Control? ",
                )
                + t("common.confirm_yes_no")
            )
            if not is_affirmative_reply(confirmation):
                logger.info(
                    tr(
                        "❌ Отключение BBR отменено пользователем",
                        "❌ BBR disable was cancelled by the user",
                    )
                )
                return True
        try:
            logger.info(
                tr(
                    "🔻 Начало отключения TCP BBR Congestion Control...",
                    "🔻 Starting TCP BBR Congestion Control disable...",
                )
            )

            logger.debug(
                tr(
                    "🔍 Проверка текущего состояния алгоритма управления перегрузками...",
                    "🔍 Checking the current congestion-control state...",
                )
            )
            current_algo = self._get_current_congestion_control()
            if current_algo == "cubic":
                logger.info(
                    tr(
                        "✅ Уже используется cubic, ничего не делаем 🎯",
                        "✅ cubic is already in use, nothing to do 🎯",
                    )
                )
                return True
            if current_algo == "bbr":
                logger.debug(
                    tr(
                        "ℹ️ Обнаружен BBR, переключаем на cubic...",
                        "ℹ️ BBR detected, switching to cubic...",
                    )
                )
            elif current_algo:
                logger.debug(
                    tr(
                        f"ℹ️ Текущий алгоритм: {current_algo}, переключаем на cubic...",
                        f"ℹ️ Current algorithm: {current_algo}, switching to cubic...",
                    )
                )
            else:
                logger.warning(
                    tr(
                        "⚠️ Не удалось определить текущий алгоритм, продолжаем...",
                        "⚠️ Failed to detect the current algorithm, continuing...",
                    )
                )

            logger.debug(
                tr(
                    "♻️ Восстановление настроек по умолчанию для алгоритма управления перегрузками...",
                    "♻️ Restoring default congestion-control settings...",
                )
            )
            if not self._write_config_file(
                self.SYSCTL_CONFIG_PATH,
                self.safe_config,
                "параметры sysctl по умолчанию",
            ):
                return False
            logger.debug(
                tr(
                    f"✅ Восстановлен конфиг: {self.SYSCTL_CONFIG_PATH}",
                    f"✅ Restored config: {self.SYSCTL_CONFIG_PATH}",
                )
            )

            logger.debug(tr("🔄 Применение настроек sysctl...", "🔄 Applying sysctl settings..."))

            cc_result = run(["sysctl", "-w", self.CUBIC], check=False)
            logger.debug(
                tr(
                    f"⚙️ congestion_control: {cc_result.stdout.strip()}",
                    f"⚙️ congestion_control: {cc_result.stdout.strip()}",
                )
            )
            if cc_result.returncode != 0:
                logger.warning(
                    tr(
                        "⚠️ Не удалось применить net.ipv4.tcp_congestion_control=cubic",
                        "⚠️ Failed to apply net.ipv4.tcp_congestion_control=cubic",
                    )
                )

            qdisc_result = run(["sysctl", "-w", self.FQ_CODEL], check=False)
            logger.debug(
                tr(
                    f"⚙️ qdisc: {qdisc_result.stdout.strip()}",
                    f"⚙️ qdisc: {qdisc_result.stdout.strip()}",
                )
            )
            if qdisc_result.returncode != 0:
                logger.warning(
                    tr(
                        "⚠️ Не удалось применить net.core.default_qdisc=fq_codel",
                        "⚠️ Failed to apply net.core.default_qdisc=fq_codel",
                    )
                )

            logger.debug(tr("🔍 Финальная проверка...", "🔍 Final verification..."))
            final_algo = self._get_current_congestion_control()

            if final_algo == "cubic":
                logger.info(
                    tr(
                        "✅ TCP BBR Congestion Control выключен, восстановлен алгоритм cubic 🎯",
                        "✅ TCP BBR Congestion Control disabled, cubic algorithm restored 🎯",
                    )
                )
                return True
            if final_algo == "bbr":
                logger.error(
                    tr(
                        "❌ BBR всё ещё активен после отключения",
                        "❌ BBR is still active after disabling",
                    )
                )
                return False
            if final_algo:
                logger.warning(
                    tr(
                        f"⚠️ Установлен алгоритм '{final_algo}' (ожидалось 'cubic')",
                        f"⚠️ Algorithm '{final_algo}' is active (expected 'cubic')",
                    )
                )
                return False

            logger.warning(
                tr(
                    "⚠️ Не удалось проверить текущий алгоритм после отключения",
                    "⚠️ Failed to verify the current algorithm after disabling",
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
                    "💥 Критическая ошибка при отключении BBR",
                    "💥 Critical error while disabling BBR",
                )
            )
            return False
