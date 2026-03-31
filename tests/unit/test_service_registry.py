from unittest.mock import MagicMock, patch

from app.core import service_registry
from app.i18n.locale import set_locale
from app.interfaces.menu.menu_utils import MenuItem


def test_service_registry_codes_are_unique():
    set_locale("ru")
    codes = [entry.code for entry in service_registry.get_service_registry()]
    assert len(codes) == len(set(codes))


def test_service_registry_lookup_returns_entry_by_code():
    set_locale("ru")
    entry = service_registry.get_service_entry("3")

    assert entry is not None
    assert entry.name == "Docker"


def test_service_registry_help_text_is_generated_from_registry():
    set_locale("ru")
    help_text = service_registry.format_service_codes_help()

    assert help_text.startswith("1=UFW")
    assert "6=UV" in help_text


def test_service_registry_uses_concise_main_menu_labels():
    set_locale("ru")
    entries = {entry.key: entry for entry in service_registry.get_service_registry()}

    assert entries["ufw"].main_menu_label == "1 - 🔥 UFW - межсетевой экран"
    assert entries["bbr"].main_menu_label == "2 - 🌐 BBR - ускорение сети"


def test_build_main_menu_items_uses_registry_entries():
    service = MagicMock()
    action = MagicMock()
    entry = service_registry.ServiceRegistryEntry(
        code="9",
        key="demo",
        name="Demo",
        cli_label="9=Demo",
        icon="🧪",
        main_menu_description_key="menu.registry.docker_description",
        service_import="demo.service.Factory",
        interactive_import="demo.interactive.run",
        main_menu_status_renderer=lambda current_service: (
            "🟢 ready" if current_service is service else "🔴 broken"
        ),
    )

    with (
        patch.object(service_registry, "SERVICE_REGISTRY", (entry,)),
        patch(
            "app.core.service_registry._load_attr",
            side_effect=[MagicMock(return_value=service), action],
        ),
    ):
        items = service_registry.build_main_menu_items()

    assert len(items) == 1
    assert isinstance(items[0], MenuItem)
    assert items[0].key == "9"
    assert items[0].label == "9 - 🧪 Demo - установка контейнеризации"
    assert items[0].status_renderer is not None
    assert items[0].status_renderer() == "🟢 ready"


def test_service_registry_switches_main_menu_labels_to_english():
    set_locale("en")
    entries = {entry.key: entry for entry in service_registry.get_service_registry()}

    assert entries["ufw"].main_menu_label == "1 - 🔥 UFW - firewall"
    assert entries["bbr"].main_menu_label == "2 - 🌐 BBR - network acceleration"
