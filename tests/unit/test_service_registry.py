from unittest.mock import MagicMock, patch

from app.interfaces.interactive.menu_utils import MenuItem
from app.utils import service_registry


def test_service_registry_codes_are_unique():
    codes = [entry.code for entry in service_registry.get_service_registry()]
    assert len(codes) == len(set(codes))


def test_service_registry_lookup_returns_entry_by_code():
    entry = service_registry.get_service_entry("3")

    assert entry is not None
    assert entry.name == "Docker"


def test_service_registry_help_text_is_generated_from_registry():
    help_text = service_registry.format_service_codes_help()

    assert help_text.startswith("1=UFW")
    assert "6=UV" in help_text


def test_build_main_menu_items_uses_registry_entries():
    service = MagicMock()
    action = MagicMock()
    entry = service_registry.ServiceRegistryEntry(
        code="9",
        key="demo",
        name="Demo",
        cli_label="9=Demo",
        main_menu_label="9 - Demo service",
        service_import="demo.service.Factory",
        interactive_import="demo.interactive.run",
        main_menu_status_renderer=lambda current_service: (
            "🟢 ready" if current_service is service else "🔴 broken"
        ),
    )

    with (
        patch.object(service_registry, "SERVICE_REGISTRY", (entry,)),
        patch(
            "app.utils.service_registry._load_attr",
            side_effect=[MagicMock(return_value=service), action],
        ),
    ):
        items = service_registry.build_main_menu_items()

    assert len(items) == 1
    assert isinstance(items[0], MenuItem)
    assert items[0].key == "9"
    assert items[0].label == "9 - Demo service"
    assert items[0].status_renderer() == "🟢 ready"
