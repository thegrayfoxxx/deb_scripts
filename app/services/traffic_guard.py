import os
import subprocess
import time
from pathlib import Path

from app.utils.logger import get_logger
from app.utils.subprocess_utils import run
from app.utils.update_utils import update_os

logger = get_logger(__name__)


class TrafficGuardService:
    # 🔧 Константы: имена сервисов и пути
    # ✅ Исправлено: убраны пробелы в URL
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
        logger.info("🔐 Проверка фаервола...")

        # Проверяем, есть ли ufw
        ufw_check = run(["which", "ufw"], check=False)
        if ufw_check.returncode != 0:
            logger.debug("ℹ️ UFW не установлен, пропускаем проверку")
            return True

        # Проверяем статус UFW
        status_result = run(["ufw", "status"], check=False)
        if "inactive" in status_result.stdout.lower():
            logger.warning("⚠️ UFW выключен, добавляем правило SSH...")

            # Добавляем правило SSH
            allow_ssh = run(["ufw", "allow", "ssh"], check=False)
            if allow_ssh.returncode == 0:
                logger.info("✅ Правило SSH добавлено")
            else:
                logger.warning("⚠️ Не удалось добавить правило SSH")

            # Включаем UFW (неинтерактивно)
            logger.info("🔐 Включение UFW...")
            enable_result = subprocess.run(
                "echo 'y' | ufw enable",
                shell=True,
                check=False,
                env={"DEBIAN_FRONTEND": "noninteractive"},
            )
            if enable_result.returncode == 0:
                logger.info("✅ UFW включён")
            else:
                logger.warning("⚠️ Не удалось включить UFW")
        else:
            # UFW уже включён, проверяем правило SSH
            rules_result = run(["ufw", "show", "added"], check=False)
            if "22" not in rules_result.stdout and "SSH" not in rules_result.stdout:
                logger.warning("⚠️ UFW включён, но нет правила SSH — добавляем...")
                run(["ufw", "allow", "ssh"], check=False)
            else:
                logger.debug("✅ Правило SSH уже есть")

        return True

    def _is_trafficguard_installed(self) -> bool:
        """Проверяет установку по нескольким индикаторам"""
        try:
            logger.debug("🔍 Проверка наличия TrafficGuard...")

            # Индикатор 1: команда
            result = run(self.TG_VERSION_CMD, check=False)
            if result.returncode == 0:
                logger.debug(f"✅ Команда доступна: {result.stdout.strip()}")
                return True

            # Индикатор 2: служба systemd
            status = self._get_service_status()
            if status in ("active", "inactive"):
                logger.debug(f"✅ Служба {self.SERVICE_NAME} найдена (статус: {status})")
                return True

            # Индикатор 3: бинарный файл
            if Path(self.BINARY_PATH).exists():
                logger.debug(f"✅ Бинарник найден: {self.BINARY_PATH}")
                return True

            # Индикатор 4: менеджер
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

            # ✅ Если служба существует (даже inactive) — считаем, что установка прошла
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
            logger.info("🛡️ Начало установки TrafficGuard...")

            if not self._check_root():
                return False

            # 🔍 Проверка: уже установлен?
            logger.info("🔍 Проверка текущего состояния...")
            if self._is_trafficguard_installed():
                result = run(self.TG_VERSION_CMD, check=False)
                version = result.stdout.strip() if result.returncode == 0 else "unknown"
                logger.info(f"✅ TrafficGuard уже установлен: {version} 🎉")
                return True

            # 🔄 Обновление системы
            logger.info("🔄 Обновление системы...")
            update_os()

            # 📦 Зависимости
            logger.info("📦 Установка зависимостей...")
            deps = [
                "curl",
                "wget",
                "rsyslog",
                "ipset",
                "ufw",
                "grep",
                "sed",
                "coreutils",
                "whois",
                "systemd",
            ]
            run(["apt", "install", "-y"] + deps, check=False)

            # 🔐 Настройка фаервола
            self._setup_firewall_safety()

            # ⬇️ Скачивание скрипта
            logger.info("⬇️ Загрузка установочного скрипта...")
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

            # 🔧 Патчим скрипт: комментируем финальный `monitor`
            logger.info("🔧 Патчим скрипт: отключаем интерактивное меню...")
            with open(script_path, "r", encoding="utf-8", errors="ignore") as f:
                original_content = f.read()

            lines = original_content.splitlines()
            patched_lines = []

            for i, line in enumerate(lines):
                stripped = line.strip()
                # Комментируем ТОЛЬКО последнюю строку с monitor
                if stripped == "/opt/trafficguard-manager.sh monitor" and i == len(lines) - 1:
                    patched_lines.append(f"# {line}  # Disabled by auto-installer")
                    logger.debug("🔧 Закомментирована финальная строка: monitor")
                else:
                    patched_lines.append(line)

            with open(script_path, "w", encoding="utf-8") as f:
                f.write("\n".join(patched_lines) + "\n")

            # 🔧 Запуск установки
            logger.info("🔧 Запуск установки (неинтерактивный режим)...")

            install_result = subprocess.run(
                ["bash", script_path, "install"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=420,  # 7 минут
                env={
                    "DEBIAN_FRONTEND": "noninteractive",
                    "PATH": os.environ.get("PATH", ""),
                    "TERM": "dumb",
                },
            )

            # 📋 Логируем вывод скрипта
            output = install_result.stdout.strip()
            if output:
                logger.debug(f"📋 Вывод скрипта:\n{output}")

            if install_result.returncode == 0:
                logger.debug("✅ Скрипт завершён успешно")
            else:
                logger.warning(f"⚠️ Скрипт вернул код {install_result.returncode}")
                # Подсказка про частые ошибки
                if "АВАРИЙНАЯ ОСТАНОВКА" in output or "UFW" in output:
                    logger.error("🔐 Ошибка фаервола: проверь правила SSH")

            # 🧹 Очистка временного файла
            if Path(script_path).exists():
                os.remove(script_path)

            # ⏳ Проверка службы
            logger.info("⏳ Проверка службы...")
            self._wait_for_service_status("active", max_wait=30)

            # ✅ Финальная проверка по всем индикаторам
            logger.info("🔍 Финальная проверка...")
            checks = {
                "command": run(self.TG_VERSION_CMD, check=False).returncode == 0,
                "service": self._get_service_status() in ("active", "inactive"),
                "binary": Path(self.BINARY_PATH).exists(),
                "manager": Path(self.MANAGER_PATH).exists(),
            }
            logger.debug(f"📊 Результаты проверок: {checks}")

            if any(checks.values()):
                logger.info("✅ TrafficGuard установлен! 🛡️🎉")
                logger.info("💡 Для меню: rknpidor")
                logger.info("💡 Для статуса: systemctl status antiscan-aggregate")
                return True
            else:
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

    def uninstall_trafficguard(self) -> bool:
        """Удаляет TrafficGuard (идемпотентно)"""
        try:
            logger.warning("⚠️ Начало удаления TrafficGuard...")

            if not self._check_root():
                return False

            if not self._is_trafficguard_installed():
                logger.info("✅ TrafficGuard не установлен, пропускаем удаление 🧹")
                return True

            # 🛑 Остановка службы
            logger.info("🛑 Остановка службы...")
            run(["systemctl", "stop", self.SERVICE_NAME], check=False)
            run(["systemctl", "stop", self.TIMER_NAME], check=False)

            # 🔌 Отключение автозагрузки
            logger.info("🔌 Отключение автозагрузки...")
            run(["systemctl", "disable", self.SERVICE_NAME], check=False)
            run(["systemctl", "disable", self.TIMER_NAME], check=False)

            # 🗑️ Удаление через менеджер, если есть
            if Path(self.MANAGER_PATH).exists():
                logger.info("🔧 Запуск удаления через менеджер...")
                subprocess.run(
                    ["bash", self.MANAGER_PATH, "uninstall"],
                    timeout=60,
                    env={"DEBIAN_FRONTEND": "noninteractive"},
                )

            # 🧹 Ручная очистка файлов
            logger.info("🧹 Очистка файлов...")
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

            # 🔥 Очистка iptables/ipset (игнорируем ошибки, если правила уже удалены)
            run(["iptables", "-D", "INPUT", "-j", "SCANNERS-BLOCK"], check=False)
            run(["ipset", "destroy", "SCANNERS-BLOCK-V4"], check=False)
            run(["ipset", "destroy", "SCANNERS-BLOCK-V6"], check=False)

            # 🔄 Перезагрузка служб
            run(["systemctl", "daemon-reload"], check=False)
            run(["systemctl", "restart", "rsyslog"], check=False)

            # ✅ Финальная проверка
            logger.info("🔍 Финальная проверка...")
            if not self._is_trafficguard_installed():
                logger.info("✅ TrafficGuard полностью удалён 🧹")
                return True
            else:
                logger.warning("⚠️ Остались следы установки — проверьте вручную")
                return False

        except FileNotFoundError:
            logger.info("✅ TrafficGuard уже удалён 🧹")
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
            # Запускаем менеджер с аргументом monitor
            # ⚠️ Это интерактивная команда — вывод пойдёт прямо в терминал
            subprocess.run(["bash", self.MANAGER_PATH, "monitor"], check=False)
        except KeyboardInterrupt:
            logger.info("↩️ Возврат в главное меню")
        except FileNotFoundError:
            logger.error("📁 Команда не найдена")
