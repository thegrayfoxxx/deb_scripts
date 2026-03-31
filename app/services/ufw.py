import os

from app.bootstrap.logger import get_logger
from app.core.status import format_status_snapshot
from app.core.subprocess import run

logger = get_logger(__name__)


class UfwService:
    """Класс сервиса для управления межсетевым экраном UFW с настройкой общих портов."""

    SSH_PORT_ALIASES = {"22", "22/tcp", "ssh"}

    INFO_LINES = (
        "UFW - это интерфейс для управления межсетевым экраном iptables",
        "Предназначен для упрощения настройки правил межсетевого экрана",
        "Основные возможности:",
        "• Блокировка/разрешение сетевых соединений",
        "• Настройка правил для конкретных портов и служб",
        "• Защита от нежелательных входящих соединений",
        "• Управление через простые команды",
        "🔗 Официальная документация: https://help.ubuntu.com/community/UFW",
    )

    def _ensure_default_policies(self) -> bool:
        """Применяет безопасные политики по умолчанию: deny incoming, allow outgoing."""
        try:
            logger.debug(
                "🔐 Установка политик по умолчанию (входящие - запрещены, исходящие - разрешены)..."
            )
            incoming_result = run(["ufw", "default", "deny", "incoming"], check=False)
            outgoing_result = run(["ufw", "default", "allow", "outgoing"], check=False)

            if incoming_result.returncode != 0 or outgoing_result.returncode != 0:
                logger.error("❌ Не удалось применить политики UFW по умолчанию")
                return False

            logger.debug("✅ Политики по умолчанию установлены")
            return True
        except Exception:
            logger.exception("💥 Критическая ошибка при установке политик UFW по умолчанию")
            return False

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

    def is_active(self) -> bool:
        """Проверяет, включён ли UFW (публичный метод)."""
        return self._is_active()

    def activate(self) -> bool:
        """Включает UFW с безопасной конфигурацией по умолчанию."""
        return self.enable_with_ssh_only()

    def deactivate(self, confirm: bool = False) -> bool:
        """Отключает UFW без удаления пакета."""
        return self.disable(confirm=confirm)

    def get_info_lines(self) -> tuple[str, ...]:
        """Возвращает краткую информацию о сервисе для интерактивного UI."""
        return self.INFO_LINES

    def ensure_safe_baseline(self) -> bool:
        """Гарантирует безопасную базовую конфигурацию UFW для серверных сценариев."""
        if not self._ensure_default_policies():
            return False

        if not self._ensure_ssh_allowed():
            logger.error("❌ Не удалось гарантировать правило SSH")
            return False

        return True

    def install(self) -> bool:
        """Устанавливает межсетевой экран UFW с включенным базовым правилом SSH."""
        try:
            logger.info("🔥 Начало установки UFW...")

            # Check if already installed
            if self.is_installed():
                logger.info("✅ UFW уже установлен 🎉")

                # Для уже установленного UFW считаем install() идемпотентной операцией.
                # Дополнительно нормализуем безопасную базовую конфигурацию.
                return self.ensure_safe_baseline()

            # Check for root privileges
            if os.geteuid() != 0:
                logger.error("🔐 Для установки UFW требуются права суперпользователя")
                return False

            logger.debug("📦 Установка пакета UFW...")
            install_result = run(["apt", "install", "-y", "ufw"], check=False)
            if install_result.returncode == 0:
                logger.debug("✅ Пакет UFW успешно установлен")
            else:
                logger.warning("⚠️ Установка пакета UFW завершилась с предупреждением")
                logger.debug(f"apt install ufw return code: {install_result.returncode}")

            if install_result.returncode != 0:
                logger.error("❌ Failed to install UFW")
                return False

            if not self.ensure_safe_baseline():
                return False

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
            logger.debug("🔒 Добавление правила SSH (порт 22) для обеспечения безопасности...")
            allow_ssh_result = run(["ufw", "allow", "ssh"], check=False)

            if allow_ssh_result.returncode != 0:
                # Try alternative port specification
                allow_ssh_result = run(["ufw", "allow", "22"], check=False)
                if allow_ssh_result.returncode != 0:
                    logger.warning("⚠️ Не удалось добавить правило SSH")
                    return False

            logger.debug("✅ Правило SSH успешно добавлено")
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
                logger.info("✅ UFW уже включён, проверяю базовую конфигурацию...")
                return self.ensure_safe_baseline()
            # If not active, continue with enabling

            # Нормализуем базовые политики перед включением, чтобы не унаследовать
            # старую конфигурацию с блокировкой исходящего трафика.
            if not self.ensure_safe_baseline():
                logger.error("❌ Невозможно включить UFW без безопасных политик по умолчанию")
                return False

            # Enable UFW (non-interactive)
            logger.debug("🔥 Включение межсетевого экрана UFW в неинтерактивном режиме...")
            enable_result = run(["ufw", "--force", "enable"], check=False)

            if enable_result.returncode != 0:
                # В некоторых окружениях ufw может вернуть ненулевой код,
                # хотя фактически уже перешёл в состояние active.
                logger.warning("⚠️ ufw enable завершился с предупреждением, перепроверяю статус...")
                logger.debug(f"ufw enable return code: {enable_result.returncode}")
                if not self._is_active():
                    logger.error("❌ Не удалось включить UFW")
                    return False

            if not self._is_active():
                logger.error("❌ UFW не перешёл в активное состояние после включения")
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
                logger.debug(f"🌐 Открытие порта {description} ({port}) в межсетевом экране...")
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
            result = run(["ufw", "status"], check=False)
            raw_status = result.stdout.strip() if result.returncode == 0 else ""
            is_active = "status: active" in raw_status.lower()
            logger.debug(f"🔍 Статус UFW: {'✅ активен' if is_active else '❌ не активен'}")
            return is_active
        except Exception as e:
            logger.debug(f"❌ Ошибка при проверке активности UFW: {e}")
            return False

    def get_status(self) -> str:
        """Получает текущий статус UFW."""
        try:
            logger.debug("🔍 Получение текущего статуса межсетевого экрана UFW...")
            installed = self.is_installed()
            result = run(["ufw", "status"], check=False)

            if result.returncode == 0:
                raw_status = result.stdout.strip() or "недоступен"
                logger.debug(f"📊 Статус UFW: {raw_status}")
            else:
                logger.debug("❌ Не удалось получить статус UFW")
                raw_status = "недоступен"

            is_active = installed and "status: active" in raw_status.lower()

            return format_status_snapshot(
                installed=installed,
                active=is_active,
                details=[f"Вывод ufw status: {raw_status}"],
            )

        except Exception as e:
            logger.debug(f"❌ Ошибка при получении статуса UFW: {e}")
            return format_status_snapshot(
                installed=self.is_installed(),
                active=self.is_active() if self.is_installed() else False,
                details=["Вывод ufw status: ошибка получения статуса"],
            )

    def open_port(self, port: str) -> bool:
        """Открывает конкретный порт в UFW."""
        try:
            logger.debug(f"🌐 Открытие порта {port}...")
            result = run(["ufw", "allow", port], check=False)

            if result.returncode == 0:
                logger.debug(f"✅ Порт {port} успешно открыт")
                return True
            else:
                logger.warning(f"⚠️ Не удалось открыть порт {port}")
                return False
        except Exception:
            logger.exception(f"💥 Критическая ошибка при открытии порта {port}")
            return False

    def close_port(self, port: str) -> bool:
        """Удаляет правило для конкретного порта, кроме SSH."""
        normalized_port = port.strip().lower()
        if normalized_port in self.SSH_PORT_ALIASES:
            logger.warning("⚠️ Удаление правила SSH запрещено для сохранения безопасного доступа")
            return False

        try:
            logger.debug(f"🔒 Удаление правила для порта {port}...")
            result = run(["ufw", "delete", "allow", port], check=False)

            if result.returncode == 0:
                logger.debug(f"✅ Правило для порта {port} успешно удалено")
                return True

            logger.warning(f"⚠️ Не удалось удалить правило для порта {port}")
            return False
        except Exception:
            logger.exception(f"💥 Критическая ошибка при удалении правила для порта {port}")
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
