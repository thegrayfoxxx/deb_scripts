def status_badge(is_ok: bool, ok_text: str, fail_text: str) -> str:
    """Форматирует короткий статус с цветным индикатором для интерактивного меню."""
    return f"{'🟢' if is_ok else '🔴'} {ok_text if is_ok else fail_text}"


def menu_action_with_status(action_text: str, is_ok: bool, ok_text: str, fail_text: str) -> str:
    """Добавляет к пункту меню краткий статус в скобках."""
    return f"{action_text} ({status_badge(is_ok, ok_text, fail_text)})"
