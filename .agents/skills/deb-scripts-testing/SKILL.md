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
- Change localization, wording, or language selection: add or update coverage for both default `ru` behavior and `--lang en` where the behavior is user-visible.
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

## Type checks

Run `uvx ty check` when a change affects:

- service contracts or protocols
- shared helpers used across multiple modules
- public function signatures
- menu/CLI wiring where mocks and runtime types can drift

Prefer checking only the touched scope when the change is small:

```bash
uvx ty check app/services/protocols.py app/core/service_registry.py
uvx ty check app/services app/interfaces
```

Use a broader pass when refactoring shared contracts or lifecycle APIs:

```bash
uvx ty check app tests
```

Treat `ty` as a validation step, not a formatting step:

- run it after code edits and before final verification
- keep fixes focused on real type drift, not broad stylistic rewrites
- if `ty` reports unrelated pre-existing issues outside the touched scope, do not broaden the task unless asked

## Rules

- Do not broaden test edits to unrelated failures unless asked.
- Keep tests focused on observable behavior, not implementation trivia.
- When log levels change, assert the user-facing outcome or logger call that matters, not every incidental debug call.
- If a system-level command is unavailable in the current environment, stop at unit/integration plus a documented smoke check.
- If you run a new canonical full-suite coverage pass and the reported coverage changes, update the documented coverage values and coverage badge text in the same change set.
- Treat coverage numbers in documentation as release-facing data, not stale examples, once a new full run is being reported to the user.

## Post-test cleanup

- After running tests or validation, remove generated `__pycache__` directories inside this repository.
- Keep cleanup scoped to the repository only.
- Do not descend into `.venv` during cleanup at all.
- Do not delete `.venv`, `.pytest_cache`, coverage artifacts, or any non-`__pycache__` paths unless the user explicitly asks.
- Treat `.venv` as fully out of scope for post-test cleanup, including nested `__pycache__` directories inside it.

Preferred cleanup command:

```bash
find . \( -path './.venv' -o -path './.venv/*' \) -prune -o -type d -name '__pycache__' -prune -exec rm -rf {} +
```
