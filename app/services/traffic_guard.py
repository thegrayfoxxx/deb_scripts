import os
import subprocess
import time
from pathlib import Path

from app.bootstrap.logger import get_logger
from app.core.status import format_status_snapshot
from app.core.subprocess import run
from app.i18n.locale import is_affirmative_reply, t, tr
from app.services.ufw import UfwService

logger = get_logger(__name__)


class TrafficGuardService:
    def is_installed(self) -> bool:
        """Проверяет, установлен ли TrafficGuard."""
        return self._is_trafficguard_installed()

    def get_status(self) -> str:
        """Возвращает человекочитаемый статус TrafficGuard."""
        installed = self._is_trafficguard_installed()
        if not installed:
            return format_status_snapshot(installed=False)

        version_result = run(self.TG_VERSION_CMD, check=False)
        version = version_result.stdout.strip() if version_result.returncode == 0 else "unknown"
        service_status = self._get_service_status() or "unknown"
        return format_status_snapshot(
            installed=True,
            details=[
                t("status.traffic_guard_version", version=version),
                t("status.service_state", state=service_status),
            ],
        )

    def get_info_lines(self) -> tuple[str, ...]:
        """Возвращает краткую информацию о сервисе для интерактивного UI."""
        return (
            t("info.traffic_guard.line1"),
            t("info.traffic_guard.line2"),
            t("info.traffic_guard.line3"),
            t("info.traffic_guard.line4"),
            t("info.traffic_guard.line5"),
            t("info.traffic_guard.line6"),
            t("info.traffic_guard.line7"),
            t("info.traffic_guard.line8"),
            t("info.traffic_guard.line9"),
        )

    # 🔧 Константы: имена сервисов и пути
    INSTALL_SCRIPT_URL = "https://raw.githubusercontent.com/DonMatteoVPN/TrafficGuard-auto/refs/heads/main/install-trafficguard.sh"

    # ❗ Правильное имя службы (из оригинального скрипта)
    SERVICE_NAME = "antiscan-aggregate"
    SERVICE_FILE = f"/etc/systemd/system/{SERVICE_NAME}.service"
    TIMER_NAME = f"{SERVICE_NAME}.timer"

    # Пути к файлам
    MANAGER_PATH = "/opt/trafficguard-manager.sh"
    MANUAL_FILE = "/opt/trafficguard-manual.list"
    BINARY_PATH = "/usr/local/bin/traffic-guard"
    LINK_PATH = "/usr/local/bin/rknpidor"

    # Команды для проверки
    TG_VERSION_CMD = ["traffic-guard", "--version"]
    TG_STATUS_CMD = ["traffic-guard", "status"]

    def _setup_firewall_safety(self) -> bool:
        """Настраивает базовые правила фаервола для безопасной установки"""
        logger.debug(
            tr(
                "🔐 Проверка межсетевого экрана перед установкой TrafficGuard...",
                "🔐 Checking firewall state before installing TrafficGuard...",
            )
        )

        # UfwService остаётся точкой интеграции, но часть проверок делаем локально,
        # чтобы можно было безопасно использовать метод в тестовой среде.
        ufw_service = UfwService()

        try:
            ufw_check = run(["which", "ufw"], check=False)
            if ufw_check.returncode != 0:
                logger.info(
                    tr(
                        "📦 Устанавливаю UFW для безопасной установки TrafficGuard...",
                        "📦 Installing UFW for a safe TrafficGuard installation...",
                    )
                )
                if not ufw_service.install():
                    logger.error(
                        tr(
                            "❌ Не удалось установить UFW для безопасной установки TrafficGuard",
                            "❌ Failed to install UFW for a safe TrafficGuard installation",
                        )
                    )
                    return False

            status_result = run(["ufw", "status"], check=False)
            is_active = "status: active" in status_result.stdout.lower()

            if not is_active:
                logger.info(
                    tr(
                        "🔐 Включаю UFW с безопасным SSH-правилом перед установкой TrafficGuard...",
                        "🔐 Enabling UFW with a safe SSH rule before installing TrafficGuard...",
                    )
                )
                if not ufw_service.enable_with_ssh_only():
                    logger.error(
                        tr(
                            "❌ Не удалось включить UFW перед установкой TrafficGuard",
                            "❌ Failed to enable UFW before installing TrafficGuard",
                        )
                    )
                    return False
                return True

            logger.debug(
                tr(
                    "🔐 UFW уже активен, проверяю базовую конфигурацию перед установкой...",
                    "🔐 UFW is already active, checking safe baseline before installation...",
                )
            )
            if not ufw_service.ensure_safe_baseline():
                logger.error(
                    tr(
                        "❌ UFW активен, но безопасная базовая конфигурация не подтверждена",
                        "❌ UFW is active, but the safe baseline configuration was not confirmed",
                    )
                )
                return False

            return True
        except Exception as e:
            logger.warning(
                tr(
                    f"⚠️ Не удалось полностью проверить правила UFW: {e}",
                    f"⚠️ Failed to fully verify UFW rules: {e}",
                )
            )
            return False

    def _is_trafficguard_installed(self) -> bool:
        """Проверяет установку по нескольким индикаторам"""
        try:
            logger.debug(
                tr(
                    "🔍 Проверка наличия TrafficGuard...",
                    "🔍 Checking whether TrafficGuard is installed...",
                )
            )

            result = run(self.TG_VERSION_CMD, check=False)
            if result.returncode == 0:
                logger.debug(
                    tr(
                        f"✅ Команда доступна: {result.stdout.strip()}",
                        f"✅ Command available: {result.stdout.strip()}",
                    )
                )
                return True

            status = self._get_service_status()
            if status in ("active", "inactive"):
                logger.debug(
                    tr(
                        f"✅ Служба {self.SERVICE_NAME} найдена (статус: {status})",
                        f"✅ Service {self.SERVICE_NAME} found (status: {status})",
                    )
                )
                return True

            if Path(self.BINARY_PATH).exists():
                logger.debug(
                    tr(
                        f"✅ Бинарник найден: {self.BINARY_PATH}",
                        f"✅ Binary found: {self.BINARY_PATH}",
                    )
                )
                return True

            if Path(self.MANAGER_PATH).exists():
                logger.debug(
                    tr(
                        f"✅ Менеджер найден: {self.MANAGER_PATH}",
                        f"✅ Manager found: {self.MANAGER_PATH}",
                    )
                )
                return True

            logger.debug(tr("❌ TrafficGuard не обнаружен", "❌ TrafficGuard not detected"))
            return False

        except Exception as e:
            logger.debug(tr(f"❌ Ошибка при проверке: {e}", f"❌ Error while checking: {e}"))
            return False

    def _get_service_status(self) -> str | None:
        """Возвращает статус службы antiscan-aggregate"""
        try:
            logger.debug(
                tr(
                    f"🔍 Проверка статуса службы {self.SERVICE_NAME}...",
                    f"🔍 Checking status of service {self.SERVICE_NAME}...",
                )
            )
            result = run(["systemctl", "is-active", self.SERVICE_NAME], check=False)
            status = result.stdout.strip()
            logger.debug(
                tr(
                    f"📡 Статус {self.SERVICE_NAME}: {status}",
                    f"📡 Status of {self.SERVICE_NAME}: {status}",
                )
            )

            valid_statuses = (
                "active",
                "inactive",
                "failed",
                "activating",
                "deactivating",
            )
            return status if status in valid_statuses else None

        except FileNotFoundError:
            logger.debug(tr("❌ systemctl не найдена", "❌ systemctl not found"))
            return None
        except Exception as e:
            logger.debug(
                tr(f"❌ Ошибка при получении статуса: {e}", f"❌ Error while getting status: {e}")
            )
            return None

    def _wait_for_service_status(
        self, target_status: str, max_wait: int = 30, poll_interval: float = 0.5
    ) -> bool:
        """Ожидает перехода службы в целевой статус"""
        logger.debug(
            tr(
                f"⏳ Ожидание статуса '{target_status}' для {self.SERVICE_NAME}...",
                f"⏳ Waiting for status '{target_status}' for {self.SERVICE_NAME}...",
            )
        )
        start_time = time.time()

        while (time.time() - start_time) < max_wait:
            try:
                current_status = self._get_service_status()
            except Exception:
                logger.debug(
                    tr(
                        "Ошибка при проверке статуса службы, продолжаем ожидание...",
                        "Error while checking service status, continuing to wait...",
                    )
                )
                current_status = None

            if current_status in ("active", "inactive"):
                elapsed = time.time() - start_time
                logger.debug(
                    tr(
                        f"✅ Служба найдена за {elapsed:.1f}с (статус: {current_status})",
                        f"✅ Service detected in {elapsed:.1f}s (status: {current_status})",
                    )
                )
                return True

            logger.debug(
                tr(
                    f"🔄 Текущий статус: {current_status or 'unknown'}...",
                    f"🔄 Current status: {current_status or 'unknown'}...",
                )
            )
            time.sleep(poll_interval)

        elapsed = time.time() - start_time
        logger.warning(
            tr(
                f"⚠️ Таймаут ожидания службы после {elapsed:.1f}с",
                f"⚠️ Timed out waiting for the service after {elapsed:.1f}s",
            )
        )
        return False

    def _check_root(self) -> bool:
        """Проверяет права суперпользователя"""
        if os.geteuid() != 0:
            logger.error(tr("🔐 Требуется запуск от root (sudo)", "🔐 Must be run as root (sudo)"))
            return False
        return True

    def install(self) -> bool:
        """Устанавливает TrafficGuard (идемпотентно, неинтерактивно)"""
        try:
            logger.info(
                tr(
                    "🛡️ Начало установки TrafficGuard (комплексной системы защиты сервера)...",
                    "🛡️ Starting TrafficGuard installation (comprehensive server protection)...",
                )
            )

            if not self._check_root():
                return False

            logger.debug(
                tr(
                    "🔍 Проверка текущего состояния TrafficGuard...",
                    "🔍 Checking current TrafficGuard state...",
                )
            )
            if self._is_trafficguard_installed():
                result = run(self.TG_VERSION_CMD, check=False)
                version = result.stdout.strip() if result.returncode == 0 else "unknown"
                logger.info(
                    tr(
                        f"✅ TrafficGuard уже установлен: {version} 🎉",
                        f"✅ TrafficGuard is already installed: {version} 🎉",
                    )
                )
                return True

            logger.debug(
                tr(
                    "📦 Установка необходимых зависимостей для TrafficGuard...",
                    "📦 Installing required dependencies for TrafficGuard...",
                )
            )
            deps = [
                "curl",
                "wget",
                "rsyslog",
                "ipset",
                "grep",
                "sed",
                "coreutils",
                "whois",
                "systemd",
            ]
            run(["apt", "install", "-y"] + deps, check=False)

            if not self._setup_firewall_safety():
                logger.error(
                    tr(
                        "❌ Требуется активный UFW для безопасной установки TrafficGuard",
                        "❌ An active UFW is required for a safe TrafficGuard installation",
                    )
                )
                return False

            logger.info(
                tr(
                    "⬇️ Запуск официального установщика TrafficGuard...",
                    "⬇️ Running the official TrafficGuard installer...",
                )
            )
            script_path = "/tmp/install-trafficguard.sh"

            dl = run(
                [
                    "curl",
                    "-fsSL",
                    "--connect-timeout",
                    "30",
                    "--max-time",
                    "120",
                    self.INSTALL_SCRIPT_URL,
                    "-o",
                    script_path,
                ],
                check=False,
            )

            if dl.returncode != 0 or not Path(script_path).exists():
                logger.error(
                    tr("❌ Не удалось скачать скрипт", "❌ Failed to download the script")
                )
                return False

            os.chmod(script_path, 0o755)
            logger.debug(
                tr(f"✅ Скрипт загружен: {script_path}", f"✅ Script downloaded: {script_path}")
            )

            logger.debug(
                tr(
                    "🔧 Патчим скрипт: отключаем интерактивное меню для неинтерактивной установки...",
                    "🔧 Patching script: disabling interactive menu for non-interactive installation...",
                )
            )
            with open(script_path, "r", encoding="utf-8", errors="ignore") as f:
                original_content = f.read()

            lines = original_content.splitlines()
            patched_lines = []

            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped == "/opt/trafficguard-manager.sh monitor" and i == len(lines) - 1:
                    patched_lines.append(f"# {line}  # Disabled by auto-installer")
                    logger.debug(
                        tr(
                            "🔧 Закомментирована финальная строка: monitor",
                            "🔧 Commented out final line: monitor",
                        )
                    )
                else:
                    patched_lines.append(line)

            with open(script_path, "w", encoding="utf-8") as f:
                f.write("\n".join(patched_lines) + "\n")

            logger.debug(
                tr(
                    "🔧 Запуск установки TrafficGuard в неинтерактивном режиме...",
                    "🔧 Running TrafficGuard installation in non-interactive mode...",
                )
            )

            install_result = subprocess.run(
                ["bash", script_path, "install"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=420,
                env={
                    "DEBIAN_FRONTEND": "noninteractive",
                    "PATH": os.environ.get("PATH", ""),
                    "TERM": "dumb",
                },
            )

            output = install_result.stdout.strip()
            if output:
                logger.debug(tr(f"📋 Вывод скрипта:\n{output}", f"📋 Script output:\n{output}"))

            if install_result.returncode == 0:
                logger.debug(tr("✅ Скрипт завершён успешно", "✅ Script completed successfully"))
            else:
                logger.warning(
                    tr(
                        "⚠️ Установщик TrafficGuard завершился с предупреждением",
                        "⚠️ TrafficGuard installer finished with a warning",
                    )
                )
                logger.debug(
                    tr(
                        f"Код возврата установщика TrafficGuard: {install_result.returncode}",
                        f"TrafficGuard installer return code: {install_result.returncode}",
                    )
                )
                if "АВАРИЙНАЯ ОСТАНОВКА" in output or "UFW" in output:
                    logger.error(
                        tr(
                            "🔐 Ошибка фаервола: проверь правила SSH",
                            "🔐 Firewall error: check SSH rules",
                        )
                    )

            if Path(script_path).exists():
                os.remove(script_path)

            logger.debug(
                tr(
                    "⏳ Проверка запуска службы TrafficGuard...",
                    "⏳ Checking TrafficGuard service startup...",
                )
            )
            self._wait_for_service_status("active", max_wait=30)

            logger.debug(
                tr(
                    "🔍 Финальная проверка установки TrafficGuard...",
                    "🔍 Final TrafficGuard installation verification...",
                )
            )
            checks = {
                "command": run(self.TG_VERSION_CMD, check=False).returncode == 0,
                "service": self._get_service_status() in ("active", "inactive"),
                "binary": Path(self.BINARY_PATH).exists(),
                "manager": Path(self.MANAGER_PATH).exists(),
            }
            logger.debug(tr(f"📊 Результаты проверок: {checks}", f"📊 Check results: {checks}"))

            if any(checks.values()):
                logger.info(
                    tr(
                        "✅ TrafficGuard успешно установлен! 🛡️🎉",
                        "✅ TrafficGuard installed successfully! 🛡️🎉",
                    )
                )
                logger.debug(
                    tr(
                        "💡 Для запуска интерактивного меню: rknpidor",
                        "💡 To launch the interactive menu: rknpidor",
                    )
                )
                logger.debug(
                    tr(
                        "💡 Для проверки статуса: systemctl status antiscan-aggregate",
                        "💡 To check status: systemctl status antiscan-aggregate",
                    )
                )
                return True

            logger.error(
                tr(
                    "❌ Установка не удалась — ни один индикатор не сработал",
                    "❌ Installation failed — none of the indicators succeeded",
                )
            )
            return False

        except subprocess.TimeoutExpired:
            logger.error(tr("⏰ Таймаут выполнения скрипта", "⏰ Script execution timed out"))
            return False
        except FileNotFoundError as e:
            logger.error(tr(f"📁 Команда не найдена: {e}", f"📁 Command not found: {e}"))
            return False
        except PermissionError as e:
            logger.error(tr(f"🔐 Ошибка прав: {e}", f"🔐 Permission error: {e}"))
            return False
        except Exception:
            logger.exception(tr("💥 Критическая ошибка", "💥 Critical error"))
            return False

    def uninstall(self, confirm: bool = False) -> bool:
        """Удаляет TrafficGuard (идемпотентно)"""
        try:
            if confirm:
                confirmation = input(
                    tr(
                        "⚠️ Вы уверены, что хотите удалить TrafficGuard (комплексную систему защиты)? ",
                        "⚠️ Are you sure you want to remove TrafficGuard (the comprehensive protection system)? ",
                    )
                    + t("common.confirm_yes_no")
                )
                if not is_affirmative_reply(confirmation):
                    logger.info(
                        tr(
                            "❌ Удаление TrafficGuard отменено пользователем",
                            "❌ TrafficGuard removal was cancelled by the user",
                        )
                    )
                    return True

            logger.warning(
                tr(
                    "⚠️ Начало удаления TrafficGuard (комплексной системы защиты)...",
                    "⚠️ Starting TrafficGuard removal (comprehensive protection system)...",
                )
            )

            if not self._check_root():
                return False

            if not self._is_trafficguard_installed():
                logger.info(
                    tr(
                        "✅ TrafficGuard не установлен, пропускаем удаление 🧹",
                        "✅ TrafficGuard is not installed, skipping removal 🧹",
                    )
                )
                return True

            logger.debug(
                tr(
                    "🛑 Остановка службы antiscan-aggregate...",
                    "🛑 Stopping antiscan-aggregate service...",
                )
            )
            run(["systemctl", "stop", self.SERVICE_NAME], check=False)
            run(["systemctl", "stop", self.TIMER_NAME], check=False)

            logger.debug(
                tr(
                    "🔌 Отключение автозагрузки службы TrafficGuard...",
                    "🔌 Disabling TrafficGuard service autostart...",
                )
            )
            run(["systemctl", "disable", self.SERVICE_NAME], check=False)
            run(["systemctl", "disable", self.TIMER_NAME], check=False)

            if Path(self.MANAGER_PATH).exists():
                logger.debug(
                    tr(
                        "🔧 Запуск процесса удаления через встроенный менеджер...",
                        "🔧 Running removal through the built-in manager...",
                    )
                )
                subprocess.run(
                    ["bash", self.MANAGER_PATH, "uninstall"],
                    timeout=60,
                    env={"DEBIAN_FRONTEND": "noninteractive"},
                )

            logger.debug(
                tr(
                    "🧹 Очистка всех файлов и конфигураций TrafficGuard...",
                    "🧹 Cleaning all TrafficGuard files and configurations...",
                )
            )
            paths_to_remove = [
                self.BINARY_PATH,
                self.LINK_PATH,
                self.MANAGER_PATH,
                self.MANUAL_FILE,
                self.SERVICE_FILE,
                f"/etc/systemd/system/{self.TIMER_NAME}",
                "/etc/rsyslog.d/10-iptables-scanners.conf",
                "/etc/logrotate.d/iptables-scanners",
            ]
            for path in paths_to_remove:
                if Path(path).exists():
                    run(["rm", "-f", path], check=False)
                    logger.debug(tr(f"🗑️ Удалён: {path}", f"🗑️ Removed: {path}"))

            run(["iptables", "-D", "INPUT", "-j", "SCANNERS-BLOCK"], check=False)
            run(["ipset", "destroy", "SCANNERS-BLOCK-V4"], check=False)
            run(["ipset", "destroy", "SCANNERS-BLOCK-V6"], check=False)

            run(["systemctl", "daemon-reload"], check=False)
            run(["systemctl", "restart", "rsyslog"], check=False)

            logger.debug(
                tr(
                    "🔍 Финальная проверка полного удаления TrafficGuard...",
                    "🔍 Final verification of complete TrafficGuard removal...",
                )
            )
            if not self._is_trafficguard_installed():
                logger.info(
                    tr(
                        "✅ TrafficGuard полностью удалён из системы 🧹",
                        "✅ TrafficGuard was fully removed from the system 🧹",
                    )
                )
                return True

            logger.warning(
                tr(
                    "⚠️ Остались следы установки — проверьте вручную",
                    "⚠️ Installation traces remain — check manually",
                )
            )
            return False

        except FileNotFoundError:
            logger.info(
                tr(
                    "✅ TrafficGuard уже удалён из системы 🧹",
                    "✅ TrafficGuard is already removed from the system 🧹",
                )
            )
            return True
        except Exception:
            logger.exception(
                tr("💥 Критическая ошибка при удалении", "💥 Critical error during removal")
            )
            return False

    def launch_monitor(self) -> None:
        """Запускает интерактивное меню мониторинга (требует tty)"""
        logger.info(
            tr(
                "📊 Запуск меню мониторинга TrafficGuard...",
                "📊 Starting the TrafficGuard monitoring menu...",
            )
        )

        if not Path(self.MANAGER_PATH).exists():
            logger.error(
                tr(
                    "❌ Менеджер не найден. Установите TrafficGuard сначала",
                    "❌ Manager not found. Install TrafficGuard first",
                )
            )
            return

        try:
            subprocess.run(["bash", self.MANAGER_PATH, "monitor"], check=False)
        except KeyboardInterrupt:
            logger.info(
                tr("↩️ Возврат в главное меню программы", "↩️ Returning to the main program menu")
            )
        except FileNotFoundError:
            logger.error(tr("📁 Команда не найдена", "📁 Command not found"))
