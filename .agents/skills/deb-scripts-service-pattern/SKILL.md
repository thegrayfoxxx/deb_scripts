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

Add `is_active()` only when runtime health differs from package presence.

## Structure

- Public methods provide the stable interface used by CLI and interactive layers.
- Private helpers do probing, parsing, file writes, subprocess calls, and retries.
- Keep command construction and path constants near the top of the class when they are reused.

## Behavioral rules

- `install()` and `uninstall()` must be idempotent.
- A no-op success should still return `True`.
- Catch operational exceptions, log context, and return `False` on failure.
- Prefer one final verification before reporting success.

## Status rules

- `is_installed()` should answer a boolean question cheaply and predictably.
- `get_status()` should provide a short multi-line snapshot for humans.
- Do not mix status reads with warning-heavy side effects.

## Integration rules

- Services should not own menu flow.
- Services should not parse CLI args.
- Services may emit operator-oriented logs but should avoid duplicating interactive menu output.

## Related skills

- Use `deb-scripts-system-commands` when the change adds or alters subprocess behavior.
- Use `deb-scripts-logging` when changing user-visible operational messages.
- Use `deb-scripts-testing` after changing service behavior.
