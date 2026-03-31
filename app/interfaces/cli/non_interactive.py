from collections.abc import Callable, Sequence
from typing import cast

from app.bootstrap.logger import get_logger
from app.core.service_registry import (
    ServiceRegistryEntry,
    get_all_service_codes,
    get_service_entry,
)
from app.i18n.locale import t
from app.services.protocols import ActivatableServiceProtocol, ManagedServiceProtocol

logger = get_logger(__name__)

ServiceOperation = Callable[[ServiceRegistryEntry, ManagedServiceProtocol], bool | None]


def _resolve_requested_codes(
    codes: Sequence[str] | None,
    *,
    use_all: bool,
) -> list[str]:
    if codes is None:
        return []
    if use_all:
        return get_all_service_codes()
    return list(codes or [])


def _resolve_service(
    code: str, action_name: str
) -> tuple[ServiceRegistryEntry, ManagedServiceProtocol] | None:
    entry = get_service_entry(code)
    if entry is None:
        logger.error(t("cli.unknown_service_code", action_name=action_name, code=code))
        return None
    return entry, entry.service_factory()


def _report_result(entry: ServiceRegistryEntry, action_name: str, result: bool | None) -> None:
    if result is None:
        return
    badge = "✅" if result else "❌"
    print(t("cli.result_line", badge=badge, service_name=entry.name, action_name=action_name))


def _run_service_operation(
    codes: Sequence[str] | None,
    *,
    use_all: bool,
    action_name: str,
    operation: ServiceOperation,
) -> bool:
    requested_codes = _resolve_requested_codes(codes, use_all=use_all)
    if not requested_codes:
        return True

    all_ok = True
    for code in requested_codes:
        resolved = _resolve_service(code, action_name)
        if resolved is None:
            all_ok = False
            continue

        entry, service = resolved
        result = operation(entry, service)
        _report_result(entry, action_name, result)
        if result is False:
            all_ok = False

    return all_ok


def _activate_service(entry: ServiceRegistryEntry, service: ManagedServiceProtocol) -> bool:
    if not all(hasattr(service, attr) for attr in ("activate", "deactivate", "is_active")):
        logger.error(t("cli.service_not_activatable", service_name=entry.name))
        return False
    activatable_service = cast(ActivatableServiceProtocol, service)
    return activatable_service.activate()


def _deactivate_service(entry: ServiceRegistryEntry, service: ManagedServiceProtocol) -> bool:
    if not all(hasattr(service, attr) for attr in ("activate", "deactivate", "is_active")):
        logger.error(t("cli.service_not_deactivatable", service_name=entry.name))
        return False
    activatable_service = cast(ActivatableServiceProtocol, service)
    return activatable_service.deactivate(confirm=False)


def _print_service_status(entry: ServiceRegistryEntry, service: ManagedServiceProtocol) -> None:
    print(f"[{entry.name}]")
    print(service.get_status())


def _print_service_info(entry: ServiceRegistryEntry, service: ManagedServiceProtocol) -> None:
    print(f"[{entry.name}]")
    for line in service.get_info_lines():
        print(line)


def run_non_interactive_commands(app_args):
    """Run non-interactive service operations."""
    all_ok = True

    all_ok &= _run_service_operation(
        app_args.install,
        use_all=app_args.all,
        action_name=t("cli.action.install"),
        operation=lambda _entry, service: service.install(),
    )
    all_ok &= _run_service_operation(
        app_args.activate,
        use_all=app_args.all,
        action_name=t("cli.action.activate"),
        operation=_activate_service,
    )
    all_ok &= _run_service_operation(
        app_args.status,
        use_all=app_args.all,
        action_name=t("cli.action.status"),
        operation=lambda entry, service: _print_service_status(entry, service),
    )
    all_ok &= _run_service_operation(
        app_args.info,
        use_all=app_args.all,
        action_name=t("cli.action.info"),
        operation=lambda entry, service: _print_service_info(entry, service),
    )
    all_ok &= _run_service_operation(
        app_args.deactivate,
        use_all=app_args.all,
        action_name=t("cli.action.deactivate"),
        operation=_deactivate_service,
    )
    all_ok &= _run_service_operation(
        app_args.uninstall,
        use_all=app_args.all,
        action_name=t("cli.action.uninstall"),
        operation=lambda _entry, service: service.uninstall(confirm=False),
    )

    return bool(all_ok)
