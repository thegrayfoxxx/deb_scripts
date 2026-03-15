import time
from pathlib import Path

from app.utils.logger import get_logger
from app.utils.subprocess_utils import run
from app.utils.update_utils import update_os

logger = get_logger(__name__)


class Fail2BanService:
    # 🔧 Константы: пути и конфигурация
    JAIL_CONFIG_PATH = "/etc/fail2ban/jail.d/sshd.local"
    SERVICE_NAME = "fail2ban"
    JAIL_NAME = "sshd"

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
                ["systemctl", "list-unit-files", f"{self.SERVICE_NAME}.service"], check=False
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

    def install_fail2ban(self):
        """Устанавливает и настраивает Fail2Ban для защиты SSH (идемпотентно)"""
        try:
            logger.info("🛡️ Начало установки Fail2Ban...")

            # 🔍 Проверка: а может, Fail2Ban уже установлен и настроен?
            logger.info("🔍 Проверка текущего состояния...")
            if self._is_service_installed():
                if self._get_service_status() == "active" and self._is_jail_active(self.JAIL_NAME):
                    logger.info(f"✅ Fail2Ban уже установлен и jail '{self.JAIL_NAME}' активен 🎉")
                    return
                logger.info("ℹ️ Fail2Ban установлен, но требует настройки...")
            else:
                logger.info("📦 Fail2Ban не установлен, начинаем установку...")

            # 🔄 Обновление системы
            logger.info("🔄 Обновление системы перед установкой...")
            update_os()
            logger.debug("✅ Система обновлена")

            # 📦 Шаг 1: Установка пакета
            logger.info(f"📦 Установка пакета {self.SERVICE_NAME}...")
            install_result = run(["apt", "install", self.SERVICE_NAME, "-y"], check=False)
            logger.debug(f"📋 apt install вывод:\n{install_result.stdout.strip()}")

            if install_result.returncode != 0:
                logger.error("❌ Ошибка при установке fail2ban")
                return
            logger.debug("✅ Пакет fail2ban установлен")

            # 📝 Шаг 2: Создание конфигурации jail
            logger.info("📝 Создание конфигурации для защиты SSH...")
            if not self._write_config_file(
                self.JAIL_CONFIG_PATH,
                self.SSH_JAIL_CONFIG,
                f"jail конфигурация для {self.JAIL_NAME}",
            ):
                return
            logger.debug(f"✅ Конфиг записан: {self.JAIL_CONFIG_PATH}")

            # ⚙️ Шаг 3: Включение автозагрузки
            logger.info("⚙️ Включение автозагрузки fail2ban...")
            enable_result = run(["systemctl", "enable", self.SERVICE_NAME], check=False)
            if enable_result.returncode == 0:
                logger.debug("✅ Автозагрузка включена")
            else:
                logger.warning("⚠️ Не удалось включить автозагрузку (возможно, уже включена)")

            # 🔄 Шаг 4: Перезапуск службы
            logger.info("🔄 Перезапуск службы fail2ban...")
            restart_result = run(["systemctl", "restart", self.SERVICE_NAME], check=False)
            if restart_result.returncode != 0:
                logger.error("❌ Ошибка при перезапуске fail2ban")
                return
            logger.debug("✅ Служба перезапущена")

            # ⏳ Шаг 5: Ожидание запуска
            logger.info("⏳ Ожидание запуска службы...")
            if not self._wait_for_service_status("active", max_wait=30):
                logger.error("❌ Служба не запустилась в течение таймаута")
                return

            # ✅ Шаг 6: Финальная проверка
            logger.info("🔍 Финальная проверка конфигурации...")

            # Проверка статуса службы
            status_result = run(["systemctl", "status", self.SERVICE_NAME], check=False)
            logger.debug(f"📋 systemctl status:\n{status_result.stdout.strip()}")

            # Проверка jail
            if self._is_jail_active(self.JAIL_NAME):
                client_result = run(["fail2ban-client", "status", self.JAIL_NAME], check=False)
                logger.debug(f"📋 fail2ban-client status:\n{client_result.stdout.strip()}")
                logger.info(f"✅ Fail2Ban успешно установлен! Jail '{self.JAIL_NAME}' активен 🛡️🎉")
            else:
                logger.warning(
                    f"⚠️ Служба активна, но jail '{self.JAIL_NAME}' не удалось проверить"
                )

        except FileNotFoundError as e:
            logger.error(f"📁 Команда не найдена: {e}")
        except PermissionError as e:
            logger.error(f"🔐 Ошибка прав доступа (требуется root?): {e}")
        except Exception:
            logger.exception("💥 Критическая ошибка при установке Fail2Ban")

    def uninstall_fail2ban(self):
        """Полностью удаляет Fail2Ban и его конфигурацию (идемпотентно)"""
        try:
            logger.warning("⚠️ Начало удаления Fail2Ban...")

            # 🔍 Проверка: а установлен ли Fail2Ban вообще?
            logger.info("🔍 Проверка наличия Fail2Ban...")
            if not self._is_service_installed():
                logger.info("✅ Fail2Ban не установлен, пропускаем удаление 🧹")
                # Всё равно почистим конфиг на всякий случай
                run(["rm", "-f", self.JAIL_CONFIG_PATH], check=False)
                return

            # 🛑 Шаг 1: Остановка службы
            logger.info("🛑 Остановка службы fail2ban...")
            stop_result = run(["systemctl", "stop", self.SERVICE_NAME], check=False)
            if stop_result.returncode == 0:
                logger.debug("✅ Служба остановлена")
            else:
                logger.warning("⚠️ Служба уже остановлена или не найдена")

            # 🔌 Шаг 2: Отключение автозагрузки
            logger.info("🔌 Отключение автозагрузки fail2ban...")
            disable_result = run(["systemctl", "disable", self.SERVICE_NAME], check=False)
            if disable_result.returncode == 0:
                logger.debug("✅ Автозагрузка отключена")
            else:
                logger.warning("⚠️ Автозагрузка уже отключена или не найдена")

            # ⏳ Шаг 3: Ожидание полной остановки
            logger.info("⏳ Ожидание полной остановки службы...")
            self._wait_for_service_status("inactive", max_wait=15)

            # 🗑️ Шаг 4: Удаление пакета
            logger.info("🗑️ Удаление пакета fail2ban...")
            remove_result = run(["apt", "remove", self.SERVICE_NAME, "-y"], check=False)
            logger.debug(f"📋 apt remove вывод:\n{remove_result.stdout.strip()}")

            if remove_result.returncode == 0:
                logger.info("✅ Пакет fail2ban удалён")
            else:
                # Код 100 = пакет уже удалён
                if remove_result.returncode == 100:
                    logger.info("✅ Пакет fail2ban уже удалён")
                else:
                    logger.warning(
                        f"⚠️ Предупреждение при удалении пакета (код {remove_result.returncode})"
                    )

            # 🧹 Шаг 5: Очистка конфигурации
            logger.info("🧹 Очистка конфигурационных файлов...")
            run(["rm", "-f", self.JAIL_CONFIG_PATH], check=False)
            logger.debug(f"✅ Удалён конфиг {self.JAIL_CONFIG_PATH}")

            # 🔍 Шаг 6: Финальная проверка
            logger.info("🔍 Финальная проверка удаления...")
            if not self._is_service_installed():
                logger.info("✅ Fail2Ban полностью удалён 🧹")
            else:
                logger.warning("⚠️ Fail2Ban всё ещё обнаружен в системе")

        except FileNotFoundError:
            # Команда не найдена = скорее всего уже удалено
            logger.info("✅ Fail2Ban уже удалён (команда не найдена) 🧹")
        except PermissionError as e:
            logger.error(f"🔐 Ошибка прав доступа (требуется root?): {e}")
        except Exception:
            logger.exception("💥 Критическая ошибка при удалении Fail2Ban")
