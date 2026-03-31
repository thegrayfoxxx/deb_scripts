from collections.abc import Sequence

from app.i18n.locale import t


def status_badge(is_ok: bool, ok_text: str, fail_text: str) -> str:
    """Форматирует короткий статус с цветным индикатором."""
    return f"{'🟢' if is_ok else '🔴'} {ok_text if is_ok else fail_text}"


def installation_status_badge(is_installed: bool) -> str:
    """Возвращает единый бейдж статуса установки."""
    return status_badge(is_installed, t("common.installed"), t("common.not_installed"))


def activation_status_badge(is_active: bool) -> str:
    """Возвращает единый бейдж статуса активации."""
    return status_badge(is_active, t("common.activated"), t("common.not_activated"))


def format_status_snapshot(
    *,
    installed: bool,
    active: bool | None = None,
    details: Sequence[str] = (),
) -> str:
    """Форматирует единый диагностический снимок состояния сервиса."""
    lines = [t("common.status_installation", status=installation_status_badge(installed))]

    if active is not None:
        lines.append(t("common.status_activation", status=activation_status_badge(active)))

    lines.extend(details)
    return "\n".join(lines)


def menu_action_with_status(action_text: str, is_ok: bool, ok_text: str, fail_text: str) -> str:
    """Добавляет к пункту меню краткий статус в скобках."""
    return f"{action_text} ({status_badge(is_ok, ok_text, fail_text)})"
