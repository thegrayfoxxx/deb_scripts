---
name: deb-scripts-service-pattern
description: Use when implementing or refactoring service classes in deb_scripts. Covers the expected public API, private helper structure, idempotent install/uninstall behavior, status design, and how services should interact with CLI and interactive layers.
---

# Service pattern

Use this skill when editing code under `app/services/`.

## Public contract

Services should expose:

- `install()`
- `uninstall()`
- `is_installed()`
- `get_status()`
- `get_info_lines()`

Activatable services should also expose:

- `activate()`
- `deactivate()`
- `is_active()`

Use `app/services/protocols.py` as the source of truth for the current contracts.

## Structure

- Public methods provide the stable interface used by CLI and interactive layers.
- Private helpers do probing, parsing, file writes, subprocess calls, and retries.
- Keep command construction and path constants near the top of the class when they are reused.

## Behavioral rules

- `install()` and `uninstall()` must be idempotent.
- A no-op success should still return `True`.
- Catch operational exceptions, log context, and return `False` on failure.
- Prefer one final verification before reporting success.
- `activate()` and `deactivate()` should be idempotent for activatable services.

## Status rules

- `is_installed()` should answer a boolean question cheaply and predictably.
- `get_status()` should provide a short multi-line snapshot for humans.
- `get_info_lines()` should return operator-facing info used by the menu layer.
- Do not mix status reads with warning-heavy side effects.
- Return user-facing status/info text in a localizable form that works for both default `ru` and `--lang en`.

## Integration rules

- Services should not own menu flow.
- Services should not parse CLI args.
- Services may emit operator-oriented logs but should avoid duplicating interactive menu output.
- Stable user-facing wording should come from `app/i18n/messages.py` via `t(...)`; localized low-level logs may use `tr(...)`.

## Related skills

- Use `deb-scripts-system-commands` when the change adds or alters subprocess behavior.
- Use `deb-scripts-logging` when changing user-visible operational messages.
- Use `deb-scripts-testing` after changing service behavior.
