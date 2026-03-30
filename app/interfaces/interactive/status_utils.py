from app.utils.status_text import (
    status_badge,
)


def menu_action_with_status(action_text: str, is_ok: bool, ok_text: str, fail_text: str) -> str:
    """Добавляет к пункту меню краткий статус в скобках."""
    return f"{action_text} ({status_badge(is_ok, ok_text, fail_text)})"
