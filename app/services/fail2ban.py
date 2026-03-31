import time
from pathlib import Path

from app.bootstrap.logger import get_logger
from app.core.status import format_status_snapshot
from app.core.subprocess import run
from app.i18n.locale import is_affirmative_reply, t, tr

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
            logger.debug(
                tr(
                    f"🔍 Проверка статуса службы {self.SERVICE_NAME}...",
                    f"🔍 Checking status of service {self.SERVICE_NAME}...",
                )
            )
            result = run(["systemctl", "is-active", self.SERVICE_NAME], check=False)
            status = result.stdout.strip()
            logger.debug(tr(f"📡 Статус службы: {status}", f"📡 Service status: {status}"))
            return (
                status
                if status in ("active", "inactive", "failed", "activating", "deactivating")
                else None
            )
        except FileNotFoundError:
            logger.debug(tr("❌ Команда systemctl не найдена", "❌ systemctl command not found"))
            return None
        except Exception as e:
            logger.debug(
                tr(
                    f"❌ Ошибка при получении статуса: {e}",
                    f"❌ Error while retrieving status: {e}",
                )
            )
            return None

    def _is_service_installed(self) -> bool:
        """Проверяет, установлен ли пакет fail2ban"""
        try:
            logger.debug(
                tr(
                    f"🔍 Проверка наличия службы {self.SERVICE_NAME}...",
                    f"🔍 Checking presence of service {self.SERVICE_NAME}...",
                )
            )
            result = run(
                ["systemctl", "list-unit-files", f"{self.SERVICE_NAME}.service"],
                check=False,
            )
            is_installed = (
                self.SERVICE_NAME in result.stdout
                and "enabled" in result.stdout
                or "disabled" in result.stdout
            )
            logger.debug(
                tr(
                    f"📦 Служба {self.SERVICE_NAME} установлена: {is_installed}",
                    f"📦 Service {self.SERVICE_NAME} installed: {is_installed}",
                )
            )
            return is_installed
        except Exception as e:
            logger.debug(
                tr(
                    f"❌ Ошибка при проверке установки: {e}",
                    f"❌ Error while checking installation: {e}",
                )
            )
            return False

    def _is_jail_active(self, jail_name: str) -> bool:
        """Проверяет, активен ли указанный jail в fail2ban"""
        try:
            logger.debug(
                tr(
                    f"🔍 Проверка статуса jail '{jail_name}'...",
                    f"🔍 Checking status of jail '{jail_name}'...",
                )
            )
            result = run(["fail2ban-client", "status", jail_name], check=False)
            is_active = result.returncode == 0 and "Status" in result.stdout
            logger.debug(
                tr(
                    f"🛡️ Jail '{jail_name}' активен: {is_active}",
                    f"🛡️ Jail '{jail_name}' active: {is_active}",
                )
            )
            return is_active
        except FileNotFoundError:
            logger.debug(
                tr("❌ Команда fail2ban-client не найдена", "❌ fail2ban-client command not found")
            )
            return False
        except Exception as e:
            logger.debug(
                tr(f"❌ Ошибка при проверке jail: {e}", f"❌ Error while checking jail: {e}")
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
            config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(config_path, "w", encoding="utf-8") as f:
                f.write(content.strip() + "\n")
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

    def _wait_for_service_status(
        self, target_status: str, max_wait: int = 30, poll_interval: float = 0.5
    ) -> bool:
        """
        Ожидает перехода службы в целевой статус.
        Returns: True если статус достигнут, False если таймаут
        """
        logger.debug(
            tr(
                f"⏳ Ожидание статуса '{target_status}' для {self.SERVICE_NAME}...",
                f"⏳ Waiting for status '{target_status}' for {self.SERVICE_NAME}...",
            )
        )
        start_time = time.time()

        while (time.time() - start_time) < max_wait:
            current_status = self._get_service_status()
            logger.debug(
                tr(
                    f"🔄 Текущий статус: {current_status}...",
                    f"🔄 Current status: {current_status}...",
                )
            )

            if current_status == target_status:
                elapsed = time.time() - start_time
                logger.debug(
                    tr(
                        f"⏱️ Статус '{target_status}' достигнут за {elapsed:.1f}с",
                        f"⏱️ Status '{target_status}' reached in {elapsed:.1f}s",
                    )
                )
                return True
            time.sleep(poll_interval)

        elapsed = time.time() - start_time
        logger.warning(
            tr(
                f"⚠️ Таймаут ожидания статуса '{target_status}' после {elapsed:.1f}с",
                f"⚠️ Timed out waiting for status '{target_status}' after {elapsed:.1f}s",
            )
        )
        return False

    def install(self) -> bool:
        """Устанавливает пакет и конфигурацию Fail2Ban без обязательной активации."""
        try:
            logger.info(tr("📦 Подготовка Fail2Ban...", "📦 Preparing Fail2Ban..."))

            if self._is_service_installed():
                logger.info(
                    tr("✅ Fail2Ban уже установлен 🎉", "✅ Fail2Ban is already installed 🎉")
                )
            else:
                install_result = run(["apt", "install", self.SERVICE_NAME, "-y"], check=False)
                logger.debug(
                    tr(
                        f"📋 apt install вывод:\n{install_result.stdout.strip()}",
                        f"📋 apt install output:\n{install_result.stdout.strip()}",
                    )
                )
                if install_result.returncode != 0:
                    logger.error(
                        tr("❌ Ошибка при установке fail2ban", "❌ Error installing fail2ban")
                    )
                    return False

            if not self._write_config_file(
                self.JAIL_CONFIG_PATH,
                self.SSH_JAIL_CONFIG,
                f"jail конфигурация для {self.JAIL_NAME}",
            ):
                return False

            enable_result = run(["systemctl", "enable", self.SERVICE_NAME], check=False)
            if enable_result.returncode != 0:
                logger.warning(
                    tr(
                        "⚠️ Не удалось включить автозагрузку (возможно, уже включена)",
                        "⚠️ Failed to enable autostart (it may already be enabled)",
                    )
                )

            if self._is_service_installed():
                logger.info(tr("✅ Fail2Ban подготовлен", "✅ Fail2Ban is prepared"))
                return True

            logger.error(
                tr(
                    "❌ Fail2Ban не обнаружен после установки",
                    "❌ Fail2Ban was not detected after installation",
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
                    "💥 Критическая ошибка при установке Fail2Ban",
                    "💥 Critical error during Fail2Ban installation",
                )
            )
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
            confirmation = input(
                tr(
                    "⚠️ Вы уверены, что хотите отключить Fail2Ban? ",
                    "⚠️ Are you sure you want to disable Fail2Ban? ",
                )
                + t("common.confirm_yes_no")
            )
            if not is_affirmative_reply(confirmation):
                logger.info(
                    tr(
                        "❌ Отключение Fail2Ban отменено пользователем",
                        "❌ Fail2Ban disable was cancelled by the user",
                    )
                )
                return True

        try:
            logger.warning(tr("⚠️ Отключение Fail2Ban...", "⚠️ Disabling Fail2Ban..."))

            if not self._is_service_installed():
                logger.info(
                    tr(
                        "✅ Fail2Ban не установлен, нечего отключать",
                        "✅ Fail2Ban is not installed, nothing to disable",
                    )
                )
                return True

            stop_result = run(["systemctl", "stop", self.SERVICE_NAME], check=False)
            if stop_result.returncode != 0:
                logger.warning(
                    tr(
                        "⚠️ Служба уже остановлена или не найдена",
                        "⚠️ The service is already stopped or was not found",
                    )
                )

            disable_result = run(["systemctl", "disable", self.SERVICE_NAME], check=False)
            if disable_result.returncode != 0:
                logger.warning(
                    tr(
                        "⚠️ Автозагрузка уже отключена или не найдена",
                        "⚠️ Autostart is already disabled or was not found",
                    )
                )

            self._wait_for_service_status("inactive", max_wait=15)

            current_status = self._get_service_status()
            if current_status != "active":
                logger.info(tr("✅ Fail2Ban отключён", "✅ Fail2Ban is disabled"))
                return True

            logger.warning(
                tr(
                    "⚠️ Fail2Ban всё ещё активен после отключения",
                    "⚠️ Fail2Ban is still active after disabling",
                )
            )
            return False
        except FileNotFoundError:
            logger.info(
                tr(
                    "✅ Fail2Ban уже отключён (команда не найдена)",
                    "✅ Fail2Ban is already disabled (command not found)",
                )
            )
            return True
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
                    "💥 Критическая ошибка при отключении Fail2Ban",
                    "💥 Critical error while disabling Fail2Ban",
                )
            )
            return False

    def get_info_lines(self) -> tuple[str, ...]:
        """Возвращает краткую информацию о сервисе для интерактивного UI."""
        return (
            t("info.fail2ban.line1"),
            t("info.fail2ban.line2"),
            t("info.fail2ban.line3"),
            t("info.fail2ban.line4"),
            t("info.fail2ban.line5"),
            t("info.fail2ban.line6"),
            t("info.fail2ban.line7"),
            t("info.fail2ban.line8"),
            t("info.fail2ban.line9"),
        )

    def get_status(self) -> str:
        """Возвращает человекочитаемый статус Fail2Ban."""
        installed = self._is_service_installed()
        service_status = self._get_service_status() or "unknown"
        jail_active = self._is_jail_active(self.JAIL_NAME)
        return format_status_snapshot(
            installed=installed,
            active=service_status == "active" and jail_active,
            details=[
                t("status.service_state", state=service_status),
                (
                    t("status.fail2ban_jail_active", jail_name=self.JAIL_NAME)
                    if jail_active
                    else t("status.fail2ban_jail_inactive", jail_name=self.JAIL_NAME)
                ),
            ],
        )

    def activate(self) -> bool:
        """Устанавливает и активирует Fail2Ban с SSH jail по умолчанию."""
        try:
            logger.info(tr("🛡️ Начало установки Fail2Ban...", "🛡️ Starting Fail2Ban activation..."))

            if not self.install():
                return False

            logger.debug(tr("🔍 Проверка текущего состояния...", "🔍 Checking current state..."))
            if self._get_service_status() == "active" and self._is_jail_active(self.JAIL_NAME):
                logger.info(
                    tr(
                        f"✅ Fail2Ban уже активен и jail '{self.JAIL_NAME}' настроен 🎉",
                        f"✅ Fail2Ban is already active and jail '{self.JAIL_NAME}' is configured 🎉",
                    )
                )
                return True

            logger.debug(
                tr("🔄 Перезапуск службы fail2ban...", "🔄 Restarting fail2ban service...")
            )
            restart_result = run(["systemctl", "restart", self.SERVICE_NAME], check=False)
            if restart_result.returncode != 0:
                logger.error(
                    tr("❌ Ошибка при перезапуске fail2ban", "❌ Error restarting fail2ban")
                )
                return False
            logger.debug(tr("✅ Служба перезапущена", "✅ Service restarted"))

            logger.debug(
                tr("⏳ Ожидание запуска службы...", "⏳ Waiting for the service to start...")
            )
            if not self._wait_for_service_status("active", max_wait=30):
                logger.error(
                    tr(
                        "❌ Служба не запустилась в течение таймаута",
                        "❌ The service did not start before timeout",
                    )
                )
                return False

            logger.debug(
                tr(
                    "🔍 Финальная проверка конфигурации...",
                    "🔍 Final configuration verification...",
                )
            )

            status_result = run(["systemctl", "status", self.SERVICE_NAME], check=False)
            logger.debug(
                tr(
                    f"📋 systemctl status:\n{status_result.stdout.strip()}",
                    f"📋 systemctl status:\n{status_result.stdout.strip()}",
                )
            )

            if self._is_jail_active(self.JAIL_NAME):
                client_result = run(["fail2ban-client", "status", self.JAIL_NAME], check=False)
                logger.debug(
                    tr(
                        f"📋 fail2ban-client status:\n{client_result.stdout.strip()}",
                        f"📋 fail2ban-client status:\n{client_result.stdout.strip()}",
                    )
                )
                logger.info(
                    tr(
                        f"✅ Fail2Ban успешно установлен! Jail '{self.JAIL_NAME}' активен 🛡️🎉",
                        f"✅ Fail2Ban activated successfully! Jail '{self.JAIL_NAME}' is active 🛡️🎉",
                    )
                )
                return True

            logger.warning(
                tr(
                    f"⚠️ Служба активна, но jail '{self.JAIL_NAME}' не удалось проверить",
                    f"⚠️ The service is active, but jail '{self.JAIL_NAME}' could not be verified",
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
                    "💥 Критическая ошибка при установке Fail2Ban",
                    "💥 Critical error while activating Fail2Ban",
                )
            )
            return False

    def uninstall(self, confirm: bool = False) -> bool:
        """Полностью удаляет Fail2Ban и его конфигурацию (идемпотентно)"""
        try:
            if confirm:
                confirmation = input(
                    tr(
                        "⚠️ Вы уверены, что хотите удалить Fail2Ban и все его настройки? ",
                        "⚠️ Are you sure you want to remove Fail2Ban and all its settings? ",
                    )
                    + t("common.confirm_yes_no")
                )
                if not is_affirmative_reply(confirmation):
                    logger.info(
                        tr(
                            "❌ Удаление Fail2Ban отменено пользователем",
                            "❌ Fail2Ban removal was cancelled by the user",
                        )
                    )
                    return True
            logger.warning(tr("⚠️ Начало удаления Fail2Ban...", "⚠️ Starting Fail2Ban removal..."))

            logger.debug(
                tr(
                    "🔍 Проверка наличия Fail2Ban...",
                    "🔍 Checking whether Fail2Ban is installed...",
                )
            )
            if not self._is_service_installed():
                logger.info(
                    tr(
                        "✅ Fail2Ban не установлен, пропускаем удаление 🧹",
                        "✅ Fail2Ban is not installed, skipping removal 🧹",
                    )
                )
                run(["rm", "-f", self.JAIL_CONFIG_PATH], check=False)
                return True

            if not self.deactivate(confirm=False):
                logger.error(
                    tr(
                        "❌ Не удалось безопасно отключить Fail2Ban перед удалением",
                        "❌ Failed to safely disable Fail2Ban before removal",
                    )
                )
                return False

            logger.debug(tr("🗑️ Удаление пакета fail2ban...", "🗑️ Removing fail2ban package..."))
            remove_result = run(["apt", "remove", self.SERVICE_NAME, "-y"], check=False)
            logger.debug(
                tr(
                    f"📋 apt remove вывод:\n{remove_result.stdout.strip()}",
                    f"📋 apt remove output:\n{remove_result.stdout.strip()}",
                )
            )

            if remove_result.returncode == 0:
                logger.info(tr("✅ Пакет fail2ban удалён", "✅ The fail2ban package was removed"))
            elif remove_result.returncode == 100:
                logger.info(
                    tr(
                        "✅ Пакет fail2ban уже удалён",
                        "✅ The fail2ban package is already removed",
                    )
                )
            else:
                logger.warning(
                    tr(
                        "⚠️ Удаление пакета fail2ban завершилось с предупреждением",
                        "⚠️ fail2ban package removal finished with a warning",
                    )
                )
                logger.debug(
                    tr(
                        f"apt remove return code: {remove_result.returncode}",
                        f"apt remove return code: {remove_result.returncode}",
                    )
                )

            logger.debug(
                tr("🧹 Очистка конфигурационных файлов...", "🧹 Cleaning configuration files...")
            )
            run(["rm", "-f", self.JAIL_CONFIG_PATH], check=False)
            logger.debug(
                tr(
                    f"✅ Удалён конфиг {self.JAIL_CONFIG_PATH}",
                    f"✅ Removed config {self.JAIL_CONFIG_PATH}",
                )
            )

            logger.debug(
                tr("🔍 Финальная проверка удаления...", "🔍 Final removal verification...")
            )
            if not self._is_service_installed():
                logger.info(
                    tr("✅ Fail2Ban полностью удалён 🧹", "✅ Fail2Ban was fully removed 🧹")
                )
                return True

            logger.warning(
                tr(
                    "⚠️ Fail2Ban всё ещё обнаружен в системе",
                    "⚠️ Fail2Ban is still detected on the system",
                )
            )
            return False

        except FileNotFoundError:
            logger.info(
                tr(
                    "✅ Fail2Ban уже удалён (команда не найдена) 🧹",
                    "✅ Fail2Ban is already removed (command not found) 🧹",
                )
            )
            return True
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
                    "💥 Критическая ошибка при удалении Fail2Ban",
                    "💥 Critical error during Fail2Ban removal",
                )
            )
            return False
