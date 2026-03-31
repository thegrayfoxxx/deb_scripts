---
name: deb-scripts-new-service
description: Use when adding a new managed service to deb_scripts or expanding the service surface. Covers the required files, service interface contract, CLI wiring, interactive menu integration, and test updates.
---

# Add a new service

Use this skill when the task introduces a new managed component such as a firewall helper, daemon setup, package installer, or server-hardening feature.

## Related skills

- Use `deb-scripts-service-pattern` for the service class shape and public contract.
- Use `deb-scripts-system-commands` when the service adds subprocess-heavy behavior.
- Use `deb-scripts-cli-ux` for menu labels, prompts, and status wording.
- Use `deb-scripts-logging` for operator-facing logs.
- Use `deb-scripts-testing` for validation scope.

## Required files

Create:

- `app/services/<service>.py`
- `app/interfaces/menu/<service>.py`
- `tests/unit/test_<service>.py`

Add integration or system tests when the behavior interacts with real subprocesses, files, or host capabilities.

## Implementation rules

- Put operational logic in the service class.
- Follow the stable public contract from `deb-scripts-service-pattern`.
- Use shared logging and subprocess helpers.
- Keep commands idempotent and safe to rerun.
- Add `get_info_lines()` to every service.
- Add `activate()/deactivate()/is_active()` only for services whose runtime state differs from package installation.
- Add service info/status text through `app/i18n/`, not hardcoded menu constants.

## Wiring checklist

Update:

- `app/core/service_registry.py`
- `app/bootstrap/args.py`
- `app/interfaces/cli/non_interactive.py`
- `app/i18n/messages.py` for stable menu/help/status/info text

Make sure the new service gets a unique numeric code and labels in the service registry entry.

## Interactive menu checklist

- Build the submenu with the shared menu helpers.
- Keep `00` for service information.
- Keep `0` for returning back.
- Show status through shared status utilities.
- Source service info text from `service.get_info_lines()`, not a duplicated local constant.
- Do not recurse back into the main menu.
- Follow `deb-scripts-cli-ux` for wording and prompt design.
- Keep new menu labels and prompts localizable through `t(...)`.

## Test checklist

- Unit tests for service logic and status reporting.
- CLI coverage if install/uninstall routing changes.
- Integration or system tests for host-level behavior when practical.
- Use `deb-scripts-testing` to choose the minimum sufficient test set.

## Documentation

Update `README.md` when the new service changes:

- supported feature list
- CLI examples
- service code mapping
- project structure summary
