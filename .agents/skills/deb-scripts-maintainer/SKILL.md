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
- `app/interfaces/interactive/` owns menus, status screens, and user interaction only.
- `app/utils/` contains shared helpers; prefer reusing these instead of duplicating logic.

## Non-negotiable rules

- Keep system-changing operations idempotent.
- Preserve the safe UFW baseline: `deny incoming`, `allow outgoing`, and SSH access.
- Do not add `apt update/upgrade` inside individual services; OS update stays centralized in `main.py`.
- Service code logs work and failures through `app.utils.logger`.
- Interface code must not duplicate success logs already emitted by services.
- Catch specific exceptions, log useful context, and return `False` on operational failure.

## Service contract

All services should expose:

- `install()`
- `uninstall()`
- `is_installed()`
- `get_status()`

Add `is_active()` when package presence is not enough to describe runtime health.

The external API should stay uniform even if older compatibility helpers still exist internally.

## CLI and interactive conventions

- Service codes are centralized in `app/interfaces/cli/non_interactive.py`.
- If any requested operation fails, the CLI should exit non-zero.
- Interactive menus should use the loop-based helpers from `app/interfaces/interactive/menu_utils.py`.
- Prefer `build_standard_service_menu_items(...)` for service submenus.
- Service submenus must keep `00` for info and `0` for back.
- Status output should come from shared status helpers, not ad hoc string formatting.

## Editing workflow

1. Read the touched service/interface/helper modules before changing behavior.
2. Reuse existing helpers before adding new abstractions.
3. Keep business logic in services and routing/UI logic in interfaces.
4. Update `README.md` if user-facing behavior, CLI options, or supported services change.
5. Add or adjust tests with the code change.

## Validation

Follow `deb-scripts-testing` for scope selection.

Common commands:

```bash
docker compose run --rm test pytest -q --cov=app --cov=main --cov-report=term-missing
./.venv/bin/pytest -q tests/unit
./.venv/bin/pytest -q tests/integration
```
