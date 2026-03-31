---
name: deb-scripts-logging
description: Use when changing logs, CLI output, or interactive messages in deb_scripts. Covers log levels, separation between user-facing console output and debug/file logs, and CLI UX rules to avoid noisy operational telemetry.
---

# Logging policy

Use this skill whenever you touch logging, CLI output, error messaging, or interactive prompts.

## Primary goal

Make console output useful for an operator running the tool in a terminal:

- show what started
- show what completed
- show actionable warnings
- show clear failures
- hide low-level command telemetry unless debug logging is enabled

## Log level rules

- `DEBUG`: internal checks, retries, command stdout/stderr snippets, timings, return codes, path probes, state polling
- `INFO`: operation start, meaningful state transitions, successful completion, concise operator guidance
- `WARNING`: recoverable problems, degraded state, manual follow-up that may be needed
- `ERROR`: operation failed or cannot continue
- `EXCEPTION`: unexpected failures only

Do not emit low-level command return codes or repetitive "checking..." messages at `INFO`.

## CLI UX rules

- Console messages should read like operator guidance, not tracing output.
- Prefer one clear start message and one clear result message per operation.
- Avoid dumping raw command output to the console in normal runs.
- Keep extra hints short and only show them when they help the user take the next step.
- Interactive UI owns prompts and menu text; services should not duplicate that with extra chatter.
- Keep user-visible logs localizable through `app/i18n/`.

## Separation of concerns

- Interactive modules may use `print(...)` for menus, prompts, and direct status screens.
- Services should use the logger for operational events.
- If an interactive flow already prints per-item results, avoid duplicating the same success/failure through `INFO` logs in the service.
- Use `t(...)` for shared operator-facing log messages and `tr(...)` for localized low-level debug strings when a catalog key would be excessive.

## Argument model

- Prefer explicit log-level configuration over environment-style "mode" switches.
- Keep the default console level operator-friendly.
- File logging may stay more verbose than console logging.

## Validation

When refactoring logs:

1. Run targeted tests for `args_utils`, `logger`, and touched services.
2. Smoke-test one successful flow and one failure/degraded flow.
3. Confirm that normal console output is readable without debug noise.
4. If logs are user-visible, verify both default `ru` and `--lang en`.
