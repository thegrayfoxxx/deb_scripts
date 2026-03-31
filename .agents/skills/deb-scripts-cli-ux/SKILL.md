---
name: deb-scripts-cli-ux
description: Use when changing menu text, prompts, status messages, confirmations, or user-facing CLI output in deb_scripts. Covers concise operator-focused messaging, menu consistency, and avoiding duplicate or noisy output across interactive and non-interactive flows.
---

# CLI UX

Use this skill for any user-visible text in CLI or interactive flows.

## Operator-first rules

- Say what is happening, not how the code is structured.
- Prefer short, direct messages over chatty narration.
- Avoid repeating the same success/failure through both `print(...)` and service logs.
- Keep confirm prompts explicit about destructive impact.
- Route user-facing text through `app/i18n/` instead of hardcoding strings inline.
- Keep Russian as the default locale and preserve sane English output under `--lang en`.

## Menu rules

- Main and service menus should stay structurally consistent.
- Keep `00` for information and `0` for back/exit.
- Status badges should stay short and inline.
- Labels should describe the action outcome, not implementation details.

## Status text rules

- `get_status()` should be readable as a standalone diagnostic snapshot.
- Status calls should not create warning noise or side effects.
- Include only information the operator can act on.

## Message design

- Success: one compact confirmation is enough.
- Warning: tell the user what needs attention.
- Error: say what failed and, if possible, the next step.
- Extra tips should appear only when they help the user continue immediately.

## Separation

- Menus and prompts live in interactive modules.
- Operational progress and failures live in services.
- Non-interactive CLI should stay terse and predictable.
- Shared text catalogs live in `app/i18n/messages.py`; use `t(...)` for stable menu/CLI text.
- Use `tr(...)` only for localized low-level telemetry that would be too granular for the message catalog.

## Validation

- Read the output as if you were running the command over SSH on a real server.
- Remove messages that are redundant, internal, or noisy.
- If a message includes a command, make sure it is the exact next step the user should run.
- When changing wording, spot-check both default `ru` output and `--lang en`.
