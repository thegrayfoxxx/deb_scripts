from app.interfaces.interactive.status_utils import menu_action_with_status, status_badge


def test_status_badge_formats_success_and_failure():
    assert status_badge(True, "установлен", "не установлен") == "🟢 установлен"
    assert status_badge(False, "установлен", "не установлен") == "🔴 не установлен"


def test_menu_action_with_status_wraps_badge_in_parentheses():
    assert (
        menu_action_with_status("1 - 📦 Установить Docker", True, "установлен", "не установлен")
        == "1 - 📦 Установить Docker (🟢 установлен)"
    )
