import os
import subprocess
import time
from pathlib import Path

from app.services.ufw import UfwService
from app.utils.logger import get_logger
from app.utils.subprocess_utils import run

logger = get_logger(__name__)


class TrafficGuardService:
    def install(self) -> bool:
        """Единая точка входа для установки TrafficGuard."""
        return self.install_trafficguard()

    def uninstall(self, confirm: bool = False) -> bool:
        """Единая точка входа для удаления TrafficGuard."""
        return self.uninstall_trafficguard(confirm=confirm)

    def is_installed(self) -> bool:
        """Проверяет, установлен ли TrafficGuard."""
        return self._is_trafficguard_installed()

    def is_active(self) -> bool:
        """Проверяет, активна ли служба TrafficGuard."""
        return self._get_service_status() == "active"

    def get_status(self) -> str:
        """Возвращает человекочитаемый статус TrafficGuard."""
        installed = self._is_trafficguard_installed()
        if not installed:
            return "TrafficGuard: not installed"

        version_result = run(self.TG_VERSION_CMD, check=False)
        version = version_result.stdout.strip() if version_result.returncode == 0 else "unknown"
        service_status = self._get_service_status() or "unknown"
        return f"TrafficGuard: installed\nVersion: {version}\nService status: {service_status}"

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
        logger.debug("🔐 Проверка межсетевого экрана перед установкой TrafficGuard...")

        # UfwService остаётся точкой интеграции, но часть проверок делаем локально,
        # чтобы можно было безопасно использовать метод в тестовой среде.
        ufw_service = UfwService()

        try:
            ufw_check = run(["which", "ufw"], check=False)
            if ufw_check.returncode != 0:
                logger.info("📦 Устанавливаю UFW для безопасной установки TrafficGuard...")
                if not ufw_service.install():
                    logger.error(
                        "❌ Не удалось установить UFW для безопасной установки TrafficGuard"
                    )
                    return False

            status_result = run(["ufw", "status"], check=False)
            is_active = "status: active" in status_result.stdout.lower()

            if not is_active:
                logger.info(
                    "🔐 Включаю UFW с безопасным SSH-правилом перед установкой TrafficGuard..."
                )
                if not ufw_service.enable_with_ssh_only():
                    logger.error("❌ Не удалось включить UFW перед установкой TrafficGuard")
                    return False
                return True

            logger.debug("🔐 UFW уже активен, проверяю базовую конфигурацию перед установкой...")
            if not ufw_service.ensure_safe_baseline():
                logger.error("❌ UFW активен, но безопасная базовая конфигурация не подтверждена")
                return False

            return True
        except Exception as e:
            logger.warning(f"⚠️ Не удалось полностью проверить правила UFW: {e}")
            return False

    def _is_trafficguard_installed(self) -> bool:
        """Проверяет установку по нескольким индикаторам"""
        try:
            logger.debug("🔍 Проверка наличия TrafficGuard...")

            result = run(self.TG_VERSION_CMD, check=False)
            if result.returncode == 0:
                logger.debug(f"✅ Команда доступна: {result.stdout.strip()}")
                return True

            status = self._get_service_status()
            if status in ("active", "inactive"):
                logger.debug(f"✅ Служба {self.SERVICE_NAME} найдена (статус: {status})")
                return True

            if Path(self.BINARY_PATH).exists():
                logger.debug(f"✅ Бинарник найден: {self.BINARY_PATH}")
                return True

            if Path(self.MANAGER_PATH).exists():
                logger.debug(f"✅ Менеджер найден: {self.MANAGER_PATH}")
                return True

            logger.debug("❌ TrafficGuard не обнаружен")
            return False

        except Exception as e:
            logger.debug(f"❌ Ошибка при проверке: {e}")
            return False

    def _get_service_status(self) -> str | None:
        """Возвращает статус службы antiscan-aggregate"""
        try:
            logger.debug(f"🔍 Проверка статуса службы {self.SERVICE_NAME}...")
            result = run(["systemctl", "is-active", self.SERVICE_NAME], check=False)
            status = result.stdout.strip()
            logger.debug(f"📡 Статус {self.SERVICE_NAME}: {status}")

            valid_statuses = ("active", "inactive", "failed", "activating", "deactivating")
            return status if status in valid_statuses else None

        except FileNotFoundError:
            logger.debug("❌ systemctl не найдена")
            return None
        except Exception as e:
            logger.debug(f"❌ Ошибка при получении статуса: {e}")
            return None

    def _wait_for_service_status(
        self, target_status: str, max_wait: int = 30, poll_interval: float = 0.5
    ) -> bool:
        """Ожидает перехода службы в целевой статус"""
        logger.debug(f"⏳ Ожидание статуса '{target_status}' для {self.SERVICE_NAME}...")
        start_time = time.time()

        while (time.time() - start_time) < max_wait:
            try:
                current_status = self._get_service_status()
            except Exception:
                logger.debug("Ошибка при проверке статуса службы, продолжаем ожидание...")
                current_status = None

            if current_status in ("active", "inactive"):
                elapsed = time.time() - start_time
                logger.debug(f"✅ Служба найдена за {elapsed:.1f}с (статус: {current_status})")
                return True

            logger.debug(f"🔄 Текущий статус: {current_status or 'unknown'}...")
            time.sleep(poll_interval)

        elapsed = time.time() - start_time
        logger.warning(f"⚠️ Таймаут ожидания службы после {elapsed:.1f}с")
        return False

    def _check_root(self) -> bool:
        """Проверяет права суперпользователя"""
        if os.geteuid() != 0:
            logger.error("🔐 Требуется запуск от root (sudo)")
            return False
        return True

    def install_trafficguard(self) -> bool:
        """Устанавливает TrafficGuard (идемпотентно, неинтерактивно)"""
        try:
            logger.info("🛡️ Начало установки TrafficGuard (комплексной системы защиты сервера)...")

            if not self._check_root():
                return False

            logger.debug("🔍 Проверка текущего состояния TrafficGuard...")
            if self._is_trafficguard_installed():
                result = run(self.TG_VERSION_CMD, check=False)
                version = result.stdout.strip() if result.returncode == 0 else "unknown"
                logger.info(f"✅ TrafficGuard уже установлен: {version} 🎉")
                return True

            logger.debug("📦 Установка необходимых зависимостей для TrafficGuard...")
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
                logger.error("❌ Требуется активный UFW для безопасной установки TrafficGuard")
                return False

            logger.info("⬇️ Запуск официального установщика TrafficGuard...")
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
                logger.error("❌ Не удалось скачать скрипт")
                return False

            os.chmod(script_path, 0o755)
            logger.debug(f"✅ Скрипт загружен: {script_path}")

            logger.debug(
                "🔧 Патчим скрипт: отключаем интерактивное меню для неинтерактивной установки..."
            )
            with open(script_path, "r", encoding="utf-8", errors="ignore") as f:
                original_content = f.read()

            lines = original_content.splitlines()
            patched_lines = []

            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped == "/opt/trafficguard-manager.sh monitor" and i == len(lines) - 1:
                    patched_lines.append(f"# {line}  # Disabled by auto-installer")
                    logger.debug("🔧 Закомментирована финальная строка: monitor")
                else:
                    patched_lines.append(line)

            with open(script_path, "w", encoding="utf-8") as f:
                f.write("\n".join(patched_lines) + "\n")

            logger.debug("🔧 Запуск установки TrafficGuard в неинтерактивном режиме...")

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
                logger.debug(f"📋 Вывод скрипта:\n{output}")

            if install_result.returncode == 0:
                logger.debug("✅ Скрипт завершён успешно")
            else:
                logger.warning("⚠️ Установщик TrafficGuard завершился с предупреждением")
                logger.debug(f"TrafficGuard installer return code: {install_result.returncode}")
                if "АВАРИЙНАЯ ОСТАНОВКА" in output or "UFW" in output:
                    logger.error("🔐 Ошибка фаервола: проверь правила SSH")

            if Path(script_path).exists():
                os.remove(script_path)

            logger.debug("⏳ Проверка запуска службы TrafficGuard...")
            self._wait_for_service_status("active", max_wait=30)

            logger.debug("🔍 Финальная проверка установки TrafficGuard...")
            checks = {
                "command": run(self.TG_VERSION_CMD, check=False).returncode == 0,
                "service": self._get_service_status() in ("active", "inactive"),
                "binary": Path(self.BINARY_PATH).exists(),
                "manager": Path(self.MANAGER_PATH).exists(),
            }
            logger.debug(f"📊 Результаты проверок: {checks}")

            if any(checks.values()):
                logger.info("✅ TrafficGuard успешно установлен! 🛡️🎉")
                logger.debug("💡 Для запуска интерактивного меню: rknpidor")
                logger.debug("💡 Для проверки статуса: systemctl status antiscan-aggregate")
                return True

            logger.error("❌ Установка не удалась — ни один индикатор не сработал")
            return False

        except subprocess.TimeoutExpired:
            logger.error("⏰ Таймаут выполнения скрипта")
            return False
        except FileNotFoundError as e:
            logger.error(f"📁 Команда не найдена: {e}")
            return False
        except PermissionError as e:
            logger.error(f"🔐 Ошибка прав: {e}")
            return False
        except Exception:
            logger.exception("💥 Критическая ошибка")
            return False

    def uninstall_trafficguard(self, confirm: bool = False) -> bool:
        """Удаляет TrafficGuard (идемпотентно)"""
        try:
            if confirm:
                confirmation = input(
                    "⚠️ Вы уверены, что хотите удалить TrafficGuard (комплексную систему защиты)? (y/N): "
                )
                if confirmation.lower() not in ["y", "yes"]:
                    logger.info("❌ Удаление TrafficGuard отменено пользователем")
                    return True

            logger.warning("⚠️ Начало удаления TrafficGuard (комплексной системы защиты)...")

            if not self._check_root():
                return False

            if not self._is_trafficguard_installed():
                logger.info("✅ TrafficGuard не установлен, пропускаем удаление 🧹")
                return True

            logger.debug("🛑 Остановка службы antiscan-aggregate...")
            run(["systemctl", "stop", self.SERVICE_NAME], check=False)
            run(["systemctl", "stop", self.TIMER_NAME], check=False)

            logger.debug("🔌 Отключение автозагрузки службы TrafficGuard...")
            run(["systemctl", "disable", self.SERVICE_NAME], check=False)
            run(["systemctl", "disable", self.TIMER_NAME], check=False)

            if Path(self.MANAGER_PATH).exists():
                logger.debug("🔧 Запуск процесса удаления через встроенный менеджер...")
                subprocess.run(
                    ["bash", self.MANAGER_PATH, "uninstall"],
                    timeout=60,
                    env={"DEBIAN_FRONTEND": "noninteractive"},
                )

            logger.debug("🧹 Очистка всех файлов и конфигураций TrafficGuard...")
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
                    logger.debug(f"🗑️ Удалён: {path}")

            run(["iptables", "-D", "INPUT", "-j", "SCANNERS-BLOCK"], check=False)
            run(["ipset", "destroy", "SCANNERS-BLOCK-V4"], check=False)
            run(["ipset", "destroy", "SCANNERS-BLOCK-V6"], check=False)

            run(["systemctl", "daemon-reload"], check=False)
            run(["systemctl", "restart", "rsyslog"], check=False)

            logger.debug("🔍 Финальная проверка полного удаления TrafficGuard...")
            if not self._is_trafficguard_installed():
                logger.info("✅ TrafficGuard полностью удалён из системы 🧹")
                return True

            logger.warning("⚠️ Остались следы установки — проверьте вручную")
            return False

        except FileNotFoundError:
            logger.info("✅ TrafficGuard уже удалён из системы 🧹")
            return True
        except Exception:
            logger.exception("💥 Критическая ошибка при удалении")
            return False

    def launch_monitor(self) -> None:
        """Запускает интерактивное меню мониторинга (требует tty)"""
        logger.info("📊 Запуск меню мониторинга TrafficGuard...")

        if not Path(self.MANAGER_PATH).exists():
            logger.error("❌ Менеджер не найден. Установите TrafficGuard сначала")
            return

        try:
            subprocess.run(["bash", self.MANAGER_PATH, "monitor"], check=False)
        except KeyboardInterrupt:
            logger.info("↩️ Возврат в главное меню программы")
        except FileNotFoundError:
            logger.error("📁 Команда не найдена")
