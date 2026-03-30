from collections.abc import Sequence

INSTALL_OK_TEXT = "установлен"
INSTALL_FAIL_TEXT = "не установлен"
ACTIVATION_OK_TEXT = "активирован"
ACTIVATION_FAIL_TEXT = "не активирован"


def status_badge(is_ok: bool, ok_text: str, fail_text: str) -> str:
    """Форматирует короткий статус с цветным индикатором."""
    return f"{'🟢' if is_ok else '🔴'} {ok_text if is_ok else fail_text}"


def installation_status_badge(is_installed: bool) -> str:
    """Возвращает единый бейдж статуса установки."""
    return status_badge(is_installed, INSTALL_OK_TEXT, INSTALL_FAIL_TEXT)


def activation_status_badge(is_active: bool) -> str:
    """Возвращает единый бейдж статуса активации."""
    return status_badge(is_active, ACTIVATION_OK_TEXT, ACTIVATION_FAIL_TEXT)


def format_status_snapshot(
    *,
    installed: bool,
    active: bool | None = None,
    details: Sequence[str] = (),
) -> str:
    """Форматирует единый диагностический снимок состояния сервиса."""
    lines = [f"Статус установки: {installation_status_badge(installed)}"]

    if active is not None:
        lines.append(f"Статус активации: {activation_status_badge(active)}")

    lines.extend(details)
    return "\n".join(lines)
