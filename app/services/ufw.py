import os

from app.utils.logger import get_logger
from app.utils.subprocess_utils import run
from app.utils.update_utils import update_os

logger = get_logger(__name__)


class UfwService:
    """Класс сервиса для управления межсетевым экраном UFW с настройкой общих портов."""

    def _is_installed(self) -> bool:
        """Проверяет, установлен ли UFW в системе."""
        try:
            logger.debug("🔍 Проверка, установлен ли UFW...")
            result = run(["which", "ufw"], check=False)
            is_available = result.returncode == 0
            logger.debug(f"{'✅' if is_available else '❌'} Доступность UFW: {is_available}")
            return is_available
        except Exception as e:
            logger.debug(f"❌ Ошибка при проверке установки UFW: {e}")
            return False

    def is_installed(self) -> bool:
        """Проверяет, установлен ли UFW в системе (публичный метод)."""
        return self._is_installed()

    def install(self) -> bool:
        """Устанавливает межсетевой экран UFW с включенным базовым правилом SSH."""
        try:
            logger.info("🔥 Начало установки UFW...")

            # Check for root privileges
            if os.geteuid() != 0:
                logger.error("🔐 Для установки UFW требуются права суперпользователя")
                return False

            # Check if already installed
            if self._is_installed():
                logger.info("✅ UFW уже установлен 🎉")

                # Ensure SSH port is allowed if UFW is inactive
                self._ensure_ssh_allowed()
                return True

            # Update system
            logger.info("🔄 Обновление системы перед установкой UFW...")
            update_os()
            logger.debug("✅ Система обновлена перед установкой UFW")

            # Install UFW
            logger.info("📦 Установка пакета UFW...")
            install_result = run(["apt", "install", "-y", "ufw"], check=False)
            if install_result.returncode == 0:
                logger.debug("✅ Пакет UFW успешно установлен")
            else:
                logger.warning(f"⚠️ apt install вернул код {install_result.returncode}")

            if install_result.returncode != 0:
                logger.error("❌ Failed to install UFW")
                return False

            # Set default policies (deny incoming, allow outgoing)
            logger.info(
                "🔐 Установка политик по умолчанию (входящие - запрещены, исходящие - разрешены)..."
            )
            run(["ufw", "default", "deny", "incoming"], check=False)
            run(["ufw", "default", "allow", "outgoing"], check=False)
            logger.debug("✅ Политики по умолчанию установлены")

            # Allow SSH by default
            self._ensure_ssh_allowed()

            logger.info("✅ UFW успешно установлен! 🎉")
            return True

        except PermissionError as e:
            logger.error(f"🔐 Ошибка прав доступа при установке: {e}")
            return False
        except Exception:
            logger.exception("💥 Критическая ошибка при установке UFW")
            return False

    def _ensure_ssh_allowed(self) -> bool:
        """Обеспечивает разрешение порта SSH (22) перед включением UFW."""
        try:
            logger.debug("🔍 Проверка правила SSH...")

            # Check if SSH is already allowed
            show_result = run(["ufw", "show", "added"], check=False)

            if "22" in show_result.stdout or "ssh" in show_result.stdout.lower():
                logger.debug("✅ Правило SSH уже существует")
                return True

            # Add SSH rule
            logger.info("🔒 Добавление правила SSH (порт 22) для обеспечения безопасности...")
            allow_ssh_result = run(["ufw", "allow", "ssh"], check=False)

            if allow_ssh_result.returncode != 0:
                # Try alternative port specification
                allow_ssh_result = run(["ufw", "allow", "22"], check=False)
                if allow_ssh_result.returncode != 0:
                    logger.warning("⚠️ Не удалось добавить правило SSH")
                    return False

            logger.info("✅ Правило SSH успешно добавлено")
            return True

        except Exception as e:
            logger.debug(f"❌ Ошибка при обеспечении правила SSH: {e}")
            return False

    def enable_with_ssh_only(self) -> bool:
        """Включает UFW только с открытым портом SSH (безопасное значение по умолчанию)."""
        try:
            logger.info(
                "🔐 Включение межсетевого экрана UFW (только с открытым SSH для безопасности)..."
            )

            # Check if UFW is installed
            if not self._is_installed():
                logger.info("📦 UFW не установлен, устанавливаю...")
                if not self.install():
                    logger.error("❌ Не удалось установить UFW")
                    return False

            # Check if UFW is active
            if self._is_active():
                logger.info("✅ UFW уже включён")
                return True
            # If not active, continue with enabling

            # Ensure SSH is allowed
            if not self._ensure_ssh_allowed():
                logger.error("❌ Невозможно включить UFW без гарантированного доступа по SSH")
                return False

            # Enable UFW (non-interactive)
            logger.info("🔥 Включение межсетевого экрана UFW в неинтерактивном режиме...")
            enable_result = run(["ufw", "--force", "enable"], check=False)

            if enable_result.returncode != 0:
                logger.error("❌ Не удалось включить UFW")
                return False

            logger.info("✅ UFW включён с сохранением доступа по SSH")
            return True

        except Exception:
            logger.exception("💥 Критическая ошибка при включении UFW")
            return False

    def open_common_ports(self) -> bool:
        """Открывает общие порты: HTTP (80), HTTPS (443), Почта (25, 587, 993, 995)."""
        try:
            logger.info("🔓 Открытие общих портов...")

            common_ports = [
                ("80", "HTTP"),
                ("443", "HTTPS"),
                ("25", "SMTP"),
                ("587", "SMTP Submission"),
                ("993", "IMAPS"),
                ("995", "POP3S"),
            ]

            success_count = 0
            for port, description in common_ports:
                logger.info(f"🌐 Открытие порта {description} ({port}) в межсетевом экране...")
                result = run(["ufw", "allow", port], check=False)

                if result.returncode == 0:
                    logger.debug(f"✅ {description} ({port}) открыт")
                    success_count += 1
                else:
                    logger.warning(f"⚠️ Не удалось открыть {description} ({port})")

            if success_count > 0:
                logger.info(f"✅ Открыто {success_count}/{len(common_ports)} общих портов")
                return True
            else:
                logger.warning("⚠️ Ни один из общих портов не был успешно открыт")
                return False

        except Exception:
            logger.exception("💥 Критическая ошибка при открытии общих портов")
            return False

    def _is_active(self) -> bool:
        """Проверяет, активен ли UFW (включён)."""
        try:
            status = self.get_status()
            is_active = "status: active" in status.lower()
            logger.debug(f"🔍 Статус UFW: {'✅ активен' if is_active else '❌ не активен'}")
            return is_active
        except Exception as e:
            logger.debug(f"❌ Ошибка при проверке активности UFW: {e}")
            return False

    def get_status(self) -> str:
        """Получает текущий статус UFW."""
        try:
            logger.debug("🔍 Получение текущего статуса межсетевого экрана UFW...")
            result = run(["ufw", "status"], check=False)

            if result.returncode == 0:
                status = result.stdout.strip()
                logger.debug(f"📊 Статус UFW: {status}")
                return status
            else:
                logger.debug("❌ Не удалось получить статус UFW")
                return "unknown"

        except Exception as e:
            logger.debug(f"❌ Ошибка при получении статуса UFW: {e}")
            return "error"

    def open_port(self, port: str) -> bool:
        """Открывает конкретный порт в UFW."""
        try:
            logger.info(f"🌐 Открытие порта {port}...")
            result = run(["ufw", "allow", port], check=False)

            if result.returncode == 0:
                logger.info(f"✅ Порт {port} успешно открыт")
                return True
            else:
                logger.warning(f"⚠️ Не удалось открыть порт {port}")
                return False
        except Exception:
            logger.exception(f"💥 Критическая ошибка при открытии порта {port}")
            return False

    def disable(self, confirm: bool = False) -> bool:
        """Отключает межсетевой экран UFW."""
        if confirm:
            confirmation = input(
                "⚠️ Вы уверены, что хотите отключить межсетевой экран UFW? (y/N): "
            )
            if confirmation.lower() not in ["y", "yes"]:
                logger.info("❌ Отключение UFW отменено пользователем")
                return False

        try:
            logger.warning("⚠️ Отключение межсетевого экрана UFW...")

            if not self._is_installed():
                logger.info("✅ UFW не установлен, нечего отключать")
                return True

            if not self._is_active():
                logger.info("✅ UFW уже отключён")
                return True

            # Disable UFW (non-interactive)
            disable_result = run(["ufw", "disable"], check=False)

            if disable_result.returncode == 0:
                logger.info("✅ UFW успешно отключён")
                return True
            else:
                logger.error("❌ Не удалось отключить UFW")
                return False

        except Exception:
            logger.exception("💥 Критическая ошибка при отключении UFW")
            return False

    def reset(self, confirm: bool = False) -> bool:
        """Сбрасывает UFW к состоянию по умолчанию (отключает и сбрасывает правила)."""
        if confirm:
            confirmation = input(
                "⚠️ Вы уверены, что хотите сбросить UFW к настройкам по умолчанию? (y/N): "
            )
            if confirmation.lower() not in ["y", "yes"]:
                logger.info("❌ Сброс UFW отменён пользователем")
                return False

        try:
            logger.warning("⚠️ Сброс UFW к настройкам по умолчанию...")

            if not self._is_installed():
                logger.info("✅ UFW не установлен, нечего сбрасывать")
                return True

            # Disable UFW first if it's active
            if self._is_active():
                logger.info("🔒 Отключение UFW перед сбросом...")
                self.disable(confirm=False)  # Не запрашивать подтверждение дважды

            # Reset all rules (non-interactive)
            reset_result = run(["ufw", "--force", "reset"], check=False)

            if reset_result.returncode == 0:
                logger.info("✅ UFW успешно сброшен")
                return True
            else:
                logger.error("❌ Не удалось сбросить UFW")
                return False

        except Exception:
            logger.exception("💥 Критическая ошибка при сбросе UFW")
            return False

    def uninstall(self, confirm: bool = False) -> bool:
        """Удаляет межсетевой экран UFW."""
        if confirm:
            confirmation = input("⚠️ Вы уверены, что хотите удалить UFW? (y/N): ")
            if confirmation.lower() not in ["y", "yes"]:
                logger.info("❌ Удаление UFW отменено пользователем")
                return False

        try:
            logger.warning("🗑️ Начало удаления UFW...")

            if not self._is_installed():
                logger.info("✅ UFW не установлен, нечего удалять")
                return True

            # First reset UFW
            self.reset(confirm=False)  # Не запрашивать подтверждение дважды

            # Remove UFW package
            logger.info("📦 Удаление пакета UFW...")
            remove_result = run(["apt", "remove", "--purge", "-y", "ufw"], check=False)

            if remove_result.returncode == 0:
                logger.info("✅ UFW успешно удалён")
                return True
            else:
                logger.error("❌ Не удалось удалить пакет UFW")
                return False

        except Exception:
            logger.exception("💥 Критическая ошибка при удалении UFW")
            return False
