import time
from pathlib import Path

from app.bootstrap.logger import get_logger
from app.core.status import format_status_snapshot
from app.core.subprocess import run

logger = get_logger(__name__)


class Fail2BanService:
    # 🔧 Константы: пути и конфигурация
    JAIL_CONFIG_PATH = "/etc/fail2ban/jail.d/sshd.local"
    SERVICE_NAME = "fail2ban"
    JAIL_NAME = "sshd"
    INFO_LINES = (
        "Fail2Ban — система автоматической защиты от атак подбора паролей и брутфорса",
        "Основные возможности:",
        "• Мониторинг логов систем и приложений",
        "• Автоматическая блокировка подозрительных IP-адресов",
        "• Защита от DDoS-атак и сканирования портов",
        "• Настраиваемые правила фильтрации",
        "• Поддержка различных сервисов (SSH, FTP, HTTP и др.)",
        "• Логирование всех действий безопасности",
        "🔗 GitHub репозиторий: https://github.com/fail2ban/fail2ban",
    )

    # 🔧 Конфигурация jail для SSH (вынесена в константу)
    SSH_JAIL_CONFIG = """[sshd]
enabled = true
backend = systemd
journalmatch = _SYSTEMD_UNIT=ssh.service
maxretry = 5
port = ssh
bantime = 1d
findtime = 1h
"""

    def _get_service_status(self) -> str | None:
        """
        Возвращает статус службы через systemctl is-active.
        Returns: 'active', 'inactive', 'failed' или None при ошибке
        """
        try:
            logger.debug(f"🔍 Проверка статуса службы {self.SERVICE_NAME}...")
            result = run(["systemctl", "is-active", self.SERVICE_NAME], check=False)
            status = result.stdout.strip()
            logger.debug(f"📡 Статус службы: {status}")
            return (
                status
                if status in ("active", "inactive", "failed", "activating", "deactivating")
                else None
            )
        except FileNotFoundError:
            logger.debug("❌ Команда systemctl не найдена")
            return None
        except Exception as e:
            logger.debug(f"❌ Ошибка при получении статуса: {e}")
            return None

    def _is_service_installed(self) -> bool:
        """Проверяет, установлен ли пакет fail2ban"""
        try:
            logger.debug(f"🔍 Проверка наличия службы {self.SERVICE_NAME}...")
            result = run(
                ["systemctl", "list-unit-files", f"{self.SERVICE_NAME}.service"],
                check=False,
            )
            is_installed = (
                self.SERVICE_NAME in result.stdout
                and "enabled" in result.stdout
                or "disabled" in result.stdout
            )
            logger.debug(f"📦 Служба {self.SERVICE_NAME} установлена: {is_installed}")
            return is_installed
        except Exception as e:
            logger.debug(f"❌ Ошибка при проверке установки: {e}")
            return False

    def _is_jail_active(self, jail_name: str) -> bool:
        """Проверяет, активен ли указанный jail в fail2ban"""
        try:
            logger.debug(f"🔍 Проверка статуса jail '{jail_name}'...")
            result = run(["fail2ban-client", "status", jail_name], check=False)
            is_active = result.returncode == 0 and "Status" in result.stdout
            logger.debug(f"🛡️ Jail '{jail_name}' активен: {is_active}")
            return is_active
        except FileNotFoundError:
            logger.debug("❌ Команда fail2ban-client не найдена")
            return False
        except Exception as e:
            logger.debug(f"❌ Ошибка при проверке jail: {e}")
            return False

    def _write_config_file(self, path: str, content: str, description: str) -> bool:
        """
        Универсальный метод для записи конфигурационных файлов.
        Returns: True при успехе, False при ошибке
        """
        try:
            logger.debug(f"📝 Запись {description} в {path}...")
            config_path = Path(path)
            config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(config_path, "w", encoding="utf-8") as f:
                f.write(content.strip() + "\n")
            logger.debug(f"✅ Записано в {path}")
            return True
        except PermissionError:
            logger.error(f"🔐 Нет прав для записи в {path} (требуется root?)")
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка записи в {path}: {e}")
            return False

    def _wait_for_service_status(
        self, target_status: str, max_wait: int = 30, poll_interval: float = 0.5
    ) -> bool:
        """
        Ожидает перехода службы в целевой статус.
        Returns: True если статус достигнут, False если таймаут
        """
        logger.debug(f"⏳ Ожидание статуса '{target_status}' для {self.SERVICE_NAME}...")
        start_time = time.time()

        while (time.time() - start_time) < max_wait:
            current_status = self._get_service_status()
            logger.debug(f"🔄 Текущий статус: {current_status}...")

            if current_status == target_status:
                elapsed = time.time() - start_time
                logger.debug(f"⏱️ Статус '{target_status}' достигнут за {elapsed:.1f}с")
                return True
            time.sleep(poll_interval)

        elapsed = time.time() - start_time
        logger.warning(f"⚠️ Таймаут ожидания статуса '{target_status}' после {elapsed:.1f}с")
        return False

    def install(self) -> bool:
        """Устанавливает пакет и конфигурацию Fail2Ban без обязательной активации."""
        try:
            logger.info("📦 Подготовка Fail2Ban...")

            if self._is_service_installed():
                logger.info("✅ Fail2Ban уже установлен 🎉")
            else:
                install_result = run(["apt", "install", self.SERVICE_NAME, "-y"], check=False)
                logger.debug(f"📋 apt install вывод:\n{install_result.stdout.strip()}")
                if install_result.returncode != 0:
                    logger.error("❌ Ошибка при установке fail2ban")
                    return False

            if not self._write_config_file(
                self.JAIL_CONFIG_PATH,
                self.SSH_JAIL_CONFIG,
                f"jail конфигурация для {self.JAIL_NAME}",
            ):
                return False

            enable_result = run(["systemctl", "enable", self.SERVICE_NAME], check=False)
            if enable_result.returncode != 0:
                logger.warning("⚠️ Не удалось включить автозагрузку (возможно, уже включена)")

            if self._is_service_installed():
                logger.info("✅ Fail2Ban подготовлен")
                return True

            logger.error("❌ Fail2Ban не обнаружен после установки")
            return False
        except FileNotFoundError as e:
            logger.error(f"📁 Команда не найдена: {e}")
            return False
        except PermissionError as e:
            logger.error(f"🔐 Ошибка прав доступа (требуется root?): {e}")
            return False
        except Exception:
            logger.exception("💥 Критическая ошибка при установке Fail2Ban")
            return False

    def is_installed(self) -> bool:
        """Проверяет, установлен ли Fail2Ban."""
        return self._is_service_installed()

    def is_active(self) -> bool:
        """Проверяет, активен ли Fail2Ban и его SSH jail."""
        return self._get_service_status() == "active" and self._is_jail_active(self.JAIL_NAME)

    def deactivate(self, confirm: bool = False) -> bool:
        """Останавливает Fail2Ban без удаления пакета и конфигурации."""
        if confirm:
            confirmation = input("⚠️ Вы уверены, что хотите отключить Fail2Ban? (y/N): ")
            if confirmation.lower() not in ["y", "yes"]:
                logger.info("❌ Отключение Fail2Ban отменено пользователем")
                return True

        try:
            logger.warning("⚠️ Отключение Fail2Ban...")

            if not self._is_service_installed():
                logger.info("✅ Fail2Ban не установлен, нечего отключать")
                return True

            stop_result = run(["systemctl", "stop", self.SERVICE_NAME], check=False)
            if stop_result.returncode != 0:
                logger.warning("⚠️ Служба уже остановлена или не найдена")

            disable_result = run(["systemctl", "disable", self.SERVICE_NAME], check=False)
            if disable_result.returncode != 0:
                logger.warning("⚠️ Автозагрузка уже отключена или не найдена")

            self._wait_for_service_status("inactive", max_wait=15)

            current_status = self._get_service_status()
            if current_status != "active":
                logger.info("✅ Fail2Ban отключён")
                return True

            logger.warning("⚠️ Fail2Ban всё ещё активен после отключения")
            return False
        except FileNotFoundError:
            logger.info("✅ Fail2Ban уже отключён (команда не найдена)")
            return True
        except PermissionError as e:
            logger.error(f"🔐 Ошибка прав доступа (требуется root?): {e}")
            return False
        except Exception:
            logger.exception("💥 Критическая ошибка при отключении Fail2Ban")
            return False

    def get_info_lines(self) -> tuple[str, ...]:
        """Возвращает краткую информацию о сервисе для интерактивного UI."""
        return self.INFO_LINES

    def get_status(self) -> str:
        """Возвращает человекочитаемый статус Fail2Ban."""
        installed = self._is_service_installed()
        service_status = self._get_service_status() or "unknown"
        jail_active = self._is_jail_active(self.JAIL_NAME)
        return format_status_snapshot(
            installed=installed,
            active=service_status == "active" and jail_active,
            details=[
                f"Состояние службы: {service_status}",
                f"SSH jail '{self.JAIL_NAME}': {'активен' if jail_active else 'не активен'}",
            ],
        )

    def activate(self) -> bool:
        """Устанавливает и активирует Fail2Ban с SSH jail по умолчанию."""
        try:
            logger.info("🛡️ Начало установки Fail2Ban...")

            if not self.install():
                return False

            logger.debug("🔍 Проверка текущего состояния...")
            if self._get_service_status() == "active" and self._is_jail_active(self.JAIL_NAME):
                logger.info(f"✅ Fail2Ban уже активен и jail '{self.JAIL_NAME}' настроен 🎉")
                return True

            logger.debug("🔄 Перезапуск службы fail2ban...")
            restart_result = run(["systemctl", "restart", self.SERVICE_NAME], check=False)
            if restart_result.returncode != 0:
                logger.error("❌ Ошибка при перезапуске fail2ban")
                return False
            logger.debug("✅ Служба перезапущена")

            logger.debug("⏳ Ожидание запуска службы...")
            if not self._wait_for_service_status("active", max_wait=30):
                logger.error("❌ Служба не запустилась в течение таймаута")
                return False

            logger.debug("🔍 Финальная проверка конфигурации...")

            status_result = run(["systemctl", "status", self.SERVICE_NAME], check=False)
            logger.debug(f"📋 systemctl status:\n{status_result.stdout.strip()}")

            if self._is_jail_active(self.JAIL_NAME):
                client_result = run(["fail2ban-client", "status", self.JAIL_NAME], check=False)
                logger.debug(f"📋 fail2ban-client status:\n{client_result.stdout.strip()}")
                logger.info(f"✅ Fail2Ban успешно установлен! Jail '{self.JAIL_NAME}' активен 🛡️🎉")
                return True

            logger.warning(f"⚠️ Служба активна, но jail '{self.JAIL_NAME}' не удалось проверить")
            return False

        except FileNotFoundError as e:
            logger.error(f"📁 Команда не найдена: {e}")
            return False
        except PermissionError as e:
            logger.error(f"🔐 Ошибка прав доступа (требуется root?): {e}")
            return False
        except Exception:
            logger.exception("💥 Критическая ошибка при установке Fail2Ban")
            return False

    def uninstall(self, confirm: bool = False) -> bool:
        """Полностью удаляет Fail2Ban и его конфигурацию (идемпотентно)"""
        try:
            if confirm:
                confirmation = input(
                    "⚠️ Вы уверены, что хотите удалить Fail2Ban и все его настройки? (y/N): "
                )
                if confirmation.lower() not in ["y", "yes"]:
                    logger.info("❌ Удаление Fail2Ban отменено пользователем")
                    return True
            logger.warning("⚠️ Начало удаления Fail2Ban...")

            logger.debug("🔍 Проверка наличия Fail2Ban...")
            if not self._is_service_installed():
                logger.info("✅ Fail2Ban не установлен, пропускаем удаление 🧹")
                run(["rm", "-f", self.JAIL_CONFIG_PATH], check=False)
                return True

            if not self.deactivate(confirm=False):
                logger.error("❌ Не удалось безопасно отключить Fail2Ban перед удалением")
                return False

            logger.debug("🗑️ Удаление пакета fail2ban...")
            remove_result = run(["apt", "remove", self.SERVICE_NAME, "-y"], check=False)
            logger.debug(f"📋 apt remove вывод:\n{remove_result.stdout.strip()}")

            if remove_result.returncode == 0:
                logger.info("✅ Пакет fail2ban удалён")
            elif remove_result.returncode == 100:
                logger.info("✅ Пакет fail2ban уже удалён")
            else:
                logger.warning("⚠️ Удаление пакета fail2ban завершилось с предупреждением")
                logger.debug(f"apt remove return code: {remove_result.returncode}")

            logger.debug("🧹 Очистка конфигурационных файлов...")
            run(["rm", "-f", self.JAIL_CONFIG_PATH], check=False)
            logger.debug(f"✅ Удалён конфиг {self.JAIL_CONFIG_PATH}")

            logger.debug("🔍 Финальная проверка удаления...")
            if not self._is_service_installed():
                logger.info("✅ Fail2Ban полностью удалён 🧹")
                return True

            logger.warning("⚠️ Fail2Ban всё ещё обнаружен в системе")
            return False

        except FileNotFoundError:
            logger.info("✅ Fail2Ban уже удалён (команда не найдена) 🧹")
            return True
        except PermissionError as e:
            logger.error(f"🔐 Ошибка прав доступа (требуется root?): {e}")
            return False
        except Exception:
            logger.exception("💥 Критическая ошибка при удалении Fail2Ban")
            return False
