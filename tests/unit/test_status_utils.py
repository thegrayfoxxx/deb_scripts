from app.core.status import (
    activation_status_badge,
    format_status_snapshot,
    installation_status_badge,
    menu_action_with_status,
    status_badge,
)
from app.i18n.locale import set_locale


def test_status_badge_formats_success_and_failure():
    set_locale("ru")
    assert status_badge(True, "установлен", "не установлен") == "🟢 установлен"
    assert status_badge(False, "установлен", "не установлен") == "🔴 не установлен"


def test_menu_action_with_status_wraps_badge_in_parentheses():
    set_locale("ru")
    assert (
        menu_action_with_status("1 - 📦 Установить Docker", True, "установлен", "не установлен")
        == "1 - 📦 Установить Docker (🟢 установлен)"
    )


def test_unified_installation_and_activation_badges():
    set_locale("ru")
    assert installation_status_badge(True) == "🟢 установлен"
    assert installation_status_badge(False) == "🔴 не установлен"
    assert activation_status_badge(True) == "🟢 активирован"
    assert activation_status_badge(False) == "🔴 не активирован"


def test_format_status_snapshot_uses_unified_labels():
    set_locale("ru")
    assert format_status_snapshot(installed=True, active=False, details=["detail"]) == (
        "Статус установки: 🟢 установлен\nСтатус активации: 🔴 не активирован\ndetail"
    )


def test_format_status_snapshot_switches_to_english():
    set_locale("en")
    assert format_status_snapshot(installed=True, active=False, details=["detail"]) == (
        "Installation status: 🟢 installed\nActivation status: 🔴 not activated\ndetail"
    )
