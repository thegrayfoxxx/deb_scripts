from app.interfaces.interactive.status_utils import menu_action_with_status
from app.utils.status_text import (
    activation_status_badge,
    format_status_snapshot,
    installation_status_badge,
    status_badge,
)


def test_status_badge_formats_success_and_failure():
    assert status_badge(True, "установлен", "не установлен") == "🟢 установлен"
    assert status_badge(False, "установлен", "не установлен") == "🔴 не установлен"


def test_menu_action_with_status_wraps_badge_in_parentheses():
    assert (
        menu_action_with_status("1 - 📦 Установить Docker", True, "установлен", "не установлен")
        == "1 - 📦 Установить Docker (🟢 установлен)"
    )


def test_unified_installation_and_activation_badges():
    assert installation_status_badge(True) == "🟢 установлен"
    assert installation_status_badge(False) == "🔴 не установлен"
    assert activation_status_badge(True) == "🟢 активирован"
    assert activation_status_badge(False) == "🔴 не активирован"


def test_format_status_snapshot_uses_unified_labels():
    assert format_status_snapshot(installed=True, active=False, details=["detail"]) == (
        "Статус установки: 🟢 установлен\nСтатус активации: 🔴 не активирован\ndetail"
    )
