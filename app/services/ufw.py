import os

from app.bootstrap.logger import get_logger
from app.core.status import format_status_snapshot
from app.core.subprocess import run
from app.i18n.locale import is_affirmative_reply, t, tr

logger = get_logger(__name__)


class UfwService:
    """Класс сервиса для управления межсетевым экраном UFW с настройкой общих портов."""

    SSH_PORT_ALIASES = {"22", "22/tcp", "ssh"}

    def _ensure_default_policies(self) -> bool:
        """Применяет безопасные политики по умолчанию: deny incoming, allow outgoing."""
        try:
            logger.debug(
                tr(
                    "🔐 Установка политик по умолчанию (входящие - запрещены, исходящие - разрешены)...",
                    "🔐 Applying default policies (incoming denied, outgoing allowed)...",
                )
            )
            incoming_result = run(["ufw", "default", "deny", "incoming"], check=False)
            outgoing_result = run(["ufw", "default", "allow", "outgoing"], check=False)

            if incoming_result.returncode != 0 or outgoing_result.returncode != 0:
                logger.error(
                    tr(
                        "❌ Не удалось применить политики UFW по умолчанию",
                        "❌ Failed to apply the default UFW policies",
                    )
                )
                return False

            logger.debug(tr("✅ Политики по умолчанию установлены", "✅ Default policies applied"))
            return True
        except Exception:
            logger.exception(
                tr(
                    "💥 Критическая ошибка при установке политик UFW по умолчанию",
                    "💥 Critical error while applying default UFW policies",
                )
            )
            return False

    def _is_installed(self) -> bool:
        """Проверяет, установлен ли UFW в системе."""
        try:
            logger.debug(
                tr("🔍 Проверка, установлен ли UFW...", "🔍 Checking whether UFW is installed...")
            )
            result = run(["which", "ufw"], check=False)
            is_available = result.returncode == 0
            logger.debug(
                tr(
                    f"{'✅' if is_available else '❌'} Доступность UFW: {is_available}",
                    f"{'✅' if is_available else '❌'} UFW availability: {is_available}",
                )
            )
            return is_available
        except Exception as e:
            logger.debug(
                tr(
                    f"❌ Ошибка при проверке установки UFW: {e}",
                    f"❌ Error while checking UFW installation: {e}",
                )
            )
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
        return (
            t("info.ufw.line1"),
            t("info.ufw.line2"),
            t("info.ufw.line3"),
            t("info.ufw.line4"),
            t("info.ufw.line5"),
            t("info.ufw.line6"),
            t("info.ufw.line7"),
            t("info.ufw.line8"),
        )

    def ensure_safe_baseline(self) -> bool:
        """Гарантирует безопасную базовую конфигурацию UFW для серверных сценариев."""
        if not self._ensure_default_policies():
            return False

        if not self._ensure_ssh_allowed():
            logger.error(
                tr(
                    "❌ Не удалось гарантировать правило SSH",
                    "❌ Failed to guarantee the SSH rule",
                )
            )
            return False

        return True

    def install(self) -> bool:
        """Устанавливает межсетевой экран UFW с включенным базовым правилом SSH."""
        try:
            logger.info(tr("🔥 Начало установки UFW...", "🔥 Starting UFW installation..."))

            # Check if already installed
            if self.is_installed():
                logger.info(tr("✅ UFW уже установлен 🎉", "✅ UFW is already installed 🎉"))

                # Для уже установленного UFW считаем install() идемпотентной операцией.
                # Дополнительно нормализуем безопасную базовую конфигурацию.
                return self.ensure_safe_baseline()

            # Check for root privileges
            if os.geteuid() != 0:
                logger.error(
                    tr(
                        "🔐 Для установки UFW требуются права суперпользователя",
                        "🔐 Superuser privileges are required to install UFW",
                    )
                )
                return False

            logger.debug(tr("📦 Установка пакета UFW...", "📦 Installing UFW package..."))
            install_result = run(["apt", "install", "-y", "ufw"], check=False)
            if install_result.returncode == 0:
                logger.debug(
                    tr("✅ Пакет UFW успешно установлен", "✅ UFW package installed successfully")
                )
            else:
                logger.warning(
                    tr(
                        "⚠️ Установка пакета UFW завершилась с предупреждением",
                        "⚠️ UFW package installation finished with a warning",
                    )
                )
                logger.debug(
                    tr(
                        f"Код возврата apt install ufw: {install_result.returncode}",
                        f"apt install ufw return code: {install_result.returncode}",
                    )
                )

            if install_result.returncode != 0:
                logger.error(tr("❌ Не удалось установить UFW", "❌ Failed to install UFW"))
                return False

            if not self.ensure_safe_baseline():
                return False

            logger.info(tr("✅ UFW успешно установлен! 🎉", "✅ UFW installed successfully! 🎉"))
            return True

        except PermissionError as e:
            logger.error(
                tr(
                    f"🔐 Ошибка прав доступа при установке: {e}",
                    f"🔐 Permission error during installation: {e}",
                )
            )
            return False
        except Exception:
            logger.exception(
                tr(
                    "💥 Критическая ошибка при установке UFW",
                    "💥 Critical error during UFW installation",
                )
            )
            return False

    def _ensure_ssh_allowed(self) -> bool:
        """Обеспечивает разрешение порта SSH (22) перед включением UFW."""
        try:
            logger.debug(tr("🔍 Проверка правила SSH...", "🔍 Checking SSH rule..."))

            # Check if SSH is already allowed
            show_result = run(["ufw", "show", "added"], check=False)

            if "22" in show_result.stdout or "ssh" in show_result.stdout.lower():
                logger.debug(tr("✅ Правило SSH уже существует", "✅ SSH rule already exists"))
                return True

            # Add SSH rule
            logger.debug(
                tr(
                    "🔒 Добавление правила SSH (порт 22) для обеспечения безопасности...",
                    "🔒 Adding SSH rule (port 22) to preserve safe access...",
                )
            )
            allow_ssh_result = run(["ufw", "allow", "ssh"], check=False)

            if allow_ssh_result.returncode != 0:
                # Try alternative port specification
                allow_ssh_result = run(["ufw", "allow", "22"], check=False)
                if allow_ssh_result.returncode != 0:
                    logger.warning(
                        tr("⚠️ Не удалось добавить правило SSH", "⚠️ Failed to add the SSH rule")
                    )
                    return False

            logger.debug(tr("✅ Правило SSH успешно добавлено", "✅ SSH rule added successfully"))
            return True

        except Exception as e:
            logger.debug(
                tr(
                    f"❌ Ошибка при обеспечении правила SSH: {e}",
                    f"❌ Error while ensuring SSH rule: {e}",
                )
            )
            return False

    def enable_with_ssh_only(self) -> bool:
        """Включает UFW только с открытым портом SSH (безопасное значение по умолчанию)."""
        try:
            logger.info(
                "🔐 Включение межсетевого экрана UFW (только с открытым SSH для безопасности)..."
            )

            # Check if UFW is installed
            if not self._is_installed():
                logger.info(
                    tr(
                        "📦 UFW не установлен, устанавливаю...",
                        "📦 UFW is not installed, installing it...",
                    )
                )
                if not self.install():
                    logger.error(tr("❌ Не удалось установить UFW", "❌ Failed to install UFW"))
                    return False

            # Check if UFW is active
            if self._is_active():
                logger.info(
                    tr(
                        "✅ UFW уже включён, проверяю базовую конфигурацию...",
                        "✅ UFW is already enabled, checking the safe baseline...",
                    )
                )
                return self.ensure_safe_baseline()
            # If not active, continue with enabling

            # Нормализуем базовые политики перед включением, чтобы не унаследовать
            # старую конфигурацию с блокировкой исходящего трафика.
            if not self.ensure_safe_baseline():
                logger.error(
                    tr(
                        "❌ Невозможно включить UFW без безопасных политик по умолчанию",
                        "❌ Cannot enable UFW without safe default policies",
                    )
                )
                return False

            # Enable UFW (non-interactive)
            logger.debug(
                tr(
                    "🔥 Включение межсетевого экрана UFW в неинтерактивном режиме...",
                    "🔥 Enabling UFW firewall in non-interactive mode...",
                )
            )
            enable_result = run(["ufw", "--force", "enable"], check=False)

            if enable_result.returncode != 0:
                # В некоторых окружениях ufw может вернуть ненулевой код,
                # хотя фактически уже перешёл в состояние active.
                logger.warning(
                    tr(
                        "⚠️ ufw enable завершился с предупреждением, перепроверяю статус...",
                        "⚠️ ufw enable finished with a warning, rechecking status...",
                    )
                )
                logger.debug(
                    tr(
                        f"Код возврата ufw enable: {enable_result.returncode}",
                        f"ufw enable return code: {enable_result.returncode}",
                    )
                )
                if not self._is_active():
                    logger.error(tr("❌ Не удалось включить UFW", "❌ Failed to enable UFW"))
                    return False

            if not self._is_active():
                logger.error(
                    tr(
                        "❌ UFW не перешёл в активное состояние после включения",
                        "❌ UFW did not become active after enabling",
                    )
                )
                return False

            logger.info(
                tr(
                    "✅ UFW включён с сохранением доступа по SSH",
                    "✅ UFW enabled while preserving SSH access",
                )
            )
            return True

        except Exception:
            logger.exception(
                tr(
                    "💥 Критическая ошибка при включении UFW",
                    "💥 Critical error while enabling UFW",
                )
            )
            return False

    def open_common_ports(self) -> bool:
        """Открывает общие порты: HTTP (80), HTTPS (443), Почта (25, 587, 993, 995)."""
        try:
            logger.info(tr("🔓 Открытие общих портов...", "🔓 Opening common ports..."))

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
                logger.debug(
                    tr(
                        f"🌐 Открытие порта {description} ({port}) в межсетевом экране...",
                        f"🌐 Opening port {description} ({port}) in the firewall...",
                    )
                )
                result = run(["ufw", "allow", port], check=False)

                if result.returncode == 0:
                    logger.debug(
                        tr(
                            f"✅ {description} ({port}) открыт",
                            f"✅ {description} ({port}) opened",
                        )
                    )
                    success_count += 1
                else:
                    logger.warning(
                        tr(
                            f"⚠️ Не удалось открыть {description} ({port})",
                            f"⚠️ Failed to open {description} ({port})",
                        )
                    )

            if success_count > 0:
                logger.info(
                    tr(
                        f"✅ Открыто {success_count}/{len(common_ports)} общих портов",
                        f"✅ Opened {success_count}/{len(common_ports)} common ports",
                    )
                )
                return True
            else:
                logger.warning(
                    tr(
                        "⚠️ Ни один из общих портов не был успешно открыт",
                        "⚠️ None of the common ports were opened successfully",
                    )
                )
                return False

        except Exception:
            logger.exception(
                tr(
                    "💥 Критическая ошибка при открытии общих портов",
                    "💥 Critical error while opening common ports",
                )
            )
            return False

    def _is_active(self) -> bool:
        """Проверяет, активен ли UFW (включён)."""
        try:
            result = run(["ufw", "status"], check=False)
            raw_status = result.stdout.strip() if result.returncode == 0 else ""
            is_active = "status: active" in raw_status.lower()
            logger.debug(
                tr(
                    f"🔍 Статус UFW: {'✅ активен' if is_active else '❌ не активен'}",
                    f"🔍 UFW status: {'✅ active' if is_active else '❌ inactive'}",
                )
            )
            return is_active
        except Exception as e:
            logger.debug(
                tr(
                    f"❌ Ошибка при проверке активности UFW: {e}",
                    f"❌ Error while checking UFW activity: {e}",
                )
            )
            return False

    def get_status(self) -> str:
        """Получает текущий статус UFW."""
        try:
            logger.debug(
                tr(
                    "🔍 Получение текущего статуса межсетевого экрана UFW...",
                    "🔍 Getting current UFW firewall status...",
                )
            )
            installed = self.is_installed()
            result = run(["ufw", "status"], check=False)

            if result.returncode == 0:
                raw_status = result.stdout.strip() or t("status.unavailable")
                logger.debug(tr(f"📊 Статус UFW: {raw_status}", f"📊 UFW status: {raw_status}"))
            else:
                logger.debug(
                    tr("❌ Не удалось получить статус UFW", "❌ Failed to get UFW status")
                )
                raw_status = t("status.unavailable")

            is_active = installed and "status: active" in raw_status.lower()

            return format_status_snapshot(
                installed=installed,
                active=is_active,
                details=[t("status.ufw_output", value=raw_status)],
            )

        except Exception as e:
            logger.debug(
                tr(
                    f"❌ Ошибка при получении статуса UFW: {e}",
                    f"❌ Error while getting UFW status: {e}",
                )
            )
            return format_status_snapshot(
                installed=self.is_installed(),
                active=self.is_active() if self.is_installed() else False,
                details=[t("status.ufw_output", value=t("status.error_output"))],
            )

    def open_port(self, port: str) -> bool:
        """Открывает конкретный порт в UFW."""
        try:
            logger.debug(tr(f"🌐 Открытие порта {port}...", f"🌐 Opening port {port}..."))
            result = run(["ufw", "allow", port], check=False)

            if result.returncode == 0:
                logger.debug(
                    tr(f"✅ Порт {port} успешно открыт", f"✅ Port {port} opened successfully")
                )
                return True
            else:
                logger.warning(
                    tr(f"⚠️ Не удалось открыть порт {port}", f"⚠️ Failed to open port {port}")
                )
                return False
        except Exception:
            logger.exception(
                tr(
                    f"💥 Критическая ошибка при открытии порта {port}",
                    f"💥 Critical error while opening port {port}",
                )
            )
            return False

    def close_port(self, port: str) -> bool:
        """Удаляет правило для конкретного порта, кроме SSH."""
        normalized_port = port.strip().lower()
        if normalized_port in self.SSH_PORT_ALIASES:
            logger.warning(
                tr(
                    "⚠️ Удаление правила SSH запрещено для сохранения безопасного доступа",
                    "⚠️ Removing the SSH rule is forbidden to preserve safe access",
                )
            )
            return False

        try:
            logger.debug(
                tr(
                    f"🔒 Удаление правила для порта {port}...",
                    f"🔒 Removing rule for port {port}...",
                )
            )
            result = run(["ufw", "delete", "allow", port], check=False)

            if result.returncode == 0:
                logger.debug(
                    tr(
                        f"✅ Правило для порта {port} успешно удалено",
                        f"✅ Rule for port {port} removed successfully",
                    )
                )
                return True

            logger.warning(
                tr(
                    f"⚠️ Не удалось удалить правило для порта {port}",
                    f"⚠️ Failed to remove the rule for port {port}",
                )
            )
            return False
        except Exception:
            logger.exception(
                tr(
                    f"💥 Критическая ошибка при удалении правила для порта {port}",
                    f"💥 Critical error while removing the rule for port {port}",
                )
            )
            return False

    def disable(self, confirm: bool = False) -> bool:
        """Отключает межсетевой экран UFW."""
        if confirm:
            confirmation = input(
                tr(
                    "⚠️ Вы уверены, что хотите отключить межсетевой экран UFW? ",
                    "⚠️ Are you sure you want to disable the UFW firewall? ",
                )
                + t("common.confirm_yes_no")
            )
            if not is_affirmative_reply(confirmation):
                logger.info(
                    tr(
                        "❌ Отключение UFW отменено пользователем",
                        "❌ UFW disable was cancelled by the user",
                    )
                )
                return False

        try:
            logger.warning(
                tr("⚠️ Отключение межсетевого экрана UFW...", "⚠️ Disabling the UFW firewall...")
            )

            if not self._is_installed():
                logger.info(
                    tr(
                        "✅ UFW не установлен, нечего отключать",
                        "✅ UFW is not installed, nothing to disable",
                    )
                )
                return True

            if not self._is_active():
                logger.info(tr("✅ UFW уже отключён", "✅ UFW is already disabled"))
                return True

            # Disable UFW (non-interactive)
            disable_result = run(["ufw", "disable"], check=False)

            if disable_result.returncode == 0:
                logger.info(tr("✅ UFW успешно отключён", "✅ UFW disabled successfully"))
                return True
            else:
                logger.error(tr("❌ Не удалось отключить UFW", "❌ Failed to disable UFW"))
                return False

        except Exception:
            logger.exception(
                tr(
                    "💥 Критическая ошибка при отключении UFW",
                    "💥 Critical error while disabling UFW",
                )
            )
            return False

    def reset(self, confirm: bool = False) -> bool:
        """Сбрасывает UFW к состоянию по умолчанию (отключает и сбрасывает правила)."""
        if confirm:
            confirmation = input(
                tr(
                    "⚠️ Вы уверены, что хотите сбросить UFW к настройкам по умолчанию? ",
                    "⚠️ Are you sure you want to reset UFW to default settings? ",
                )
                + t("common.confirm_yes_no")
            )
            if not is_affirmative_reply(confirmation):
                logger.info(
                    tr(
                        "❌ Сброс UFW отменён пользователем",
                        "❌ UFW reset was cancelled by the user",
                    )
                )
                return False

        try:
            logger.warning(
                tr(
                    "⚠️ Сброс UFW к настройкам по умолчанию...",
                    "⚠️ Resetting UFW to default settings...",
                )
            )

            if not self._is_installed():
                logger.info(
                    tr(
                        "✅ UFW не установлен, нечего сбрасывать",
                        "✅ UFW is not installed, nothing to reset",
                    )
                )
                return True

            # Disable UFW first if it's active
            if self._is_active():
                logger.info(
                    tr("🔒 Отключение UFW перед сбросом...", "🔒 Disabling UFW before reset...")
                )
                self.disable(confirm=False)  # Не запрашивать подтверждение дважды

            # Reset all rules (non-interactive)
            reset_result = run(["ufw", "--force", "reset"], check=False)

            if reset_result.returncode == 0:
                logger.info(tr("✅ UFW успешно сброшен", "✅ UFW reset successfully"))
                return True
            else:
                logger.error(tr("❌ Не удалось сбросить UFW", "❌ Failed to reset UFW"))
                return False

        except Exception:
            logger.exception(
                tr("💥 Критическая ошибка при сбросе UFW", "💥 Critical error while resetting UFW")
            )
            return False

    def uninstall(self, confirm: bool = False) -> bool:
        """Удаляет межсетевой экран UFW."""
        if confirm:
            confirmation = input(
                tr(
                    "⚠️ Вы уверены, что хотите удалить UFW? ",
                    "⚠️ Are you sure you want to remove UFW? ",
                )
                + t("common.confirm_yes_no")
            )
            if not is_affirmative_reply(confirmation):
                logger.info(
                    tr(
                        "❌ Удаление UFW отменено пользователем",
                        "❌ UFW removal was cancelled by the user",
                    )
                )
                return False

        try:
            logger.warning(tr("🗑️ Начало удаления UFW...", "🗑️ Starting UFW removal..."))

            if not self._is_installed():
                logger.info(
                    tr(
                        "✅ UFW не установлен, нечего удалять",
                        "✅ UFW is not installed, nothing to remove",
                    )
                )
                return True

            # First reset UFW
            self.reset(confirm=False)  # Не запрашивать подтверждение дважды

            # Remove UFW package
            logger.info(tr("📦 Удаление пакета UFW...", "📦 Removing the UFW package..."))
            remove_result = run(["apt", "remove", "--purge", "-y", "ufw"], check=False)

            if remove_result.returncode == 0:
                logger.info(tr("✅ UFW успешно удалён", "✅ UFW removed successfully"))
                return True
            else:
                logger.error(
                    tr("❌ Не удалось удалить пакет UFW", "❌ Failed to remove the UFW package")
                )
                return False

        except Exception:
            logger.exception(
                tr(
                    "💥 Критическая ошибка при удалении UFW",
                    "💥 Critical error while removing UFW",
                )
            )
            return False
