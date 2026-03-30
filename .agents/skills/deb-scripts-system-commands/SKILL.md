---
name: deb-scripts-system-commands
description: Use when adding or changing apt, systemctl, ufw, sysctl, curl, rm, or other host-level command execution in deb_scripts. Covers safe subprocess patterns, post-command verification, and what to log versus what to keep in debug output.
---

# System commands

Use this skill whenever a change affects subprocess execution or host state.

## Command design

- Prefer explicit argument lists over shell strings.
- Use `check=False` when you need to inspect return codes and keep control of logging.
- Treat command stdout/stderr as debug material unless the user truly needs to see it.

## Safe patterns

- `apt`: verify success with return code and a follow-up state check when the package/service matters
- `systemctl`: do not trust a single `restart` or `enable`; re-check active state when behavior depends on it
- `ufw`: preserve safe baseline and SSH access before enablement
- `sysctl`: re-read the effective value after applying changes
- `rm`: prefer targeted paths and idempotent flags such as `-f` where appropriate
- `curl`: verify both return code and expected file presence when downloading installers

## Logging rules

- `INFO`: operation start and final outcome
- `DEBUG`: command output, timings, retries, exact return codes
- `WARNING`: command completed with degraded or uncertain result
- `ERROR`: command failure that prevents completion

## Verification

- Do not report success solely because a command exited `0` if the desired state is easy to verify.
- Prefer a state-based final check:
  - package/version present
  - service active/inactive as expected
  - config file written
  - binary exists

## Cleanup

- Clean temporary installers and transient files after successful or safe failure paths.
- Keep cleanup idempotent.

## Related skills

- Use `deb-scripts-service-pattern` for the surrounding service design.
- Use `deb-scripts-logging` if command telemetry changes what the user sees.
