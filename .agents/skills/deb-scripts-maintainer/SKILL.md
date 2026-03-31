---
name: deb-scripts-maintainer
description: Use when working in the deb_scripts repository on existing code, bug fixes, refactors, CLI behavior, interactive menus, logging, or documentation updates. Covers the project architecture, service contracts, safety constraints, and the expected testing workflow.
---

# deb_scripts maintainer

Use this skill for routine work in `deb_scripts`.

## Related skills

- Use `deb-scripts-logging` when changing logs, status messaging, or console output.
- Use `deb-scripts-testing` when deciding validation scope or editing tests.
- Use `deb-scripts-cli-ux` for menu text, prompts, and operator-facing wording.
- Use `deb-scripts-service-pattern` when restructuring service classes.
- Use `deb-scripts-system-commands` when changing subprocess behavior.

## Project shape

- `main.py` is the entrypoint.
- `main.py` validates root access, runs `update_os()` once, and then dispatches to CLI or interactive mode.
- `app/services/` contains operational logic.
- `app/interfaces/cli/` maps CLI requests to service methods and exit codes.
- `app/interfaces/menu/` owns menus, status screens, and user interaction only.
- `app/bootstrap/` contains startup, logging, args, and preflight helpers.
- `app/core/` contains shared application helpers and the service registry.
- `app/i18n/` contains locale state and shared message catalogs for user-visible text.

## Non-negotiable rules

- Keep system-changing operations idempotent.
- Preserve the safe UFW baseline: `deny incoming`, `allow outgoing`, and SSH access.
- Do not add `apt update/upgrade` inside individual services; OS update stays centralized in `main.py`.
- Service code logs work and failures through `app.bootstrap.logger`.
- Interface code must not duplicate success logs already emitted by services.
- Catch specific exceptions, log useful context, and return `False` on operational failure.

## Service contract

All services should expose:

- `install()`
- `uninstall()`
- `is_installed()`
- `get_status()`
- `get_info_lines()`

Activatable services should also expose:

- `activate()`
- `deactivate()`
- `is_active()`

Use `ManagedServiceProtocol` and `ActivatableServiceProtocol` in `app/services/protocols.py` as the source of truth for service capabilities.

## CLI and interactive conventions

- Service codes and menu wiring are centralized in `app/core/service_registry.py`.
- If any requested operation fails, the CLI should exit non-zero.
- Interactive menus should use the loop-based helpers from `app/interfaces/menu/menu_utils.py`.
- Prefer `build_standard_service_menu_items(...)` for service submenus.
- Service submenus must keep `00` for info and `0` for back.
- Status output should come from shared status helpers, not ad hoc string formatting.
- User-visible text should come from `app/i18n/messages.py` through `t(...)` whenever the wording is stable and reused.
- Use `tr(...)` from `app/i18n/locale.py` only for localized low-level telemetry where dedicated message keys would add noise.

## Editing workflow

1. Read the touched service/interface/helper modules before changing behavior.
2. Reuse existing helpers before adding new abstractions.
3. Keep business logic in services and routing/UI logic in interfaces.
4. Update `README.md` if user-facing behavior, CLI options, or supported services change.
5. Add or adjust tests with the code change.
6. When changing text, verify that the default `ru` flow and `--lang en` both stay coherent.
7. If the project version changes, update the version references in the documentation in the same change set.
8. If a new full-test coverage result becomes the canonical reported value, update the coverage references in the documentation and badges in the same change set.

## Validation

Follow `deb-scripts-testing` for scope selection.

Common commands:

```bash
docker compose run --rm test pytest -q --cov=app --cov=main --cov-report=term-missing
./.venv/bin/pytest -q tests/unit
./.venv/bin/pytest -q tests/integration
```
