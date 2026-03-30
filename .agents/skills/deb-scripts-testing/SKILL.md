---
name: deb-scripts-testing
description: Use when adding or changing tests in deb_scripts, or when deciding how to validate a code change. Covers unit, integration, and system test selection, expected smoke checks, and how to verify CLI and interactive behavior without over-testing unrelated paths.
---

# Testing workflow

Use this skill whenever behavior changes or when you need to decide what to validate.

## Test selection

- `tests/unit/`: logic inside services, helpers, logger, args parsing, CLI routing, menu rendering
- `tests/integration/`: cross-module flows, interface-to-service wiring, realistic subprocess interactions
- `tests/system/`: host-dependent behavior, root/systemd/sysctl/ufw/apt expectations

## Default expectation

- Fix or refactor inside one service: update unit tests first.
- Change CLI routing, args, exit codes, or app startup: add unit coverage for those paths.
- Change interactive menus, menu labels, or status rendering: add unit tests for menu behavior and integration tests for flows if needed.
- Change real command orchestration or install/uninstall sequencing: add integration coverage; add system coverage only when the behavior depends on the real host.

## Minimal validation by change type

- Service logic change:
  - touched service unit tests
  - related status API tests if status text changed
- CLI/logging/args change:
  - `test_args_utils.py`
  - `test_logger.py`
  - `test_cli_mode.py`
  - `test_main.py` if startup behavior changed
- Interactive UX change:
  - `test_interactive_run.py`
  - `test_interactive_status_menus.py`
  - `tests/integration/test_interactive_interfaces.py` when flow wiring changes

## Smoke checks

Prefer one live smoke check after passing unit tests:

- one success path
- one degraded/failure path if the change touched error handling

Examples:

```bash
./.venv/bin/pytest -q tests/unit/test_uv_service.py
./.venv/bin/pytest -q tests/unit/test_cli_mode.py tests/unit/test_main.py
```

## Rules

- Do not broaden test edits to unrelated failures unless asked.
- Keep tests focused on observable behavior, not implementation trivia.
- When log levels change, assert the user-facing outcome or logger call that matters, not every incidental debug call.
- If a system-level command is unavailable in the current environment, stop at unit/integration plus a documented smoke check.
