# deb_scripts Documentation

`deb_scripts` is a Python-based toolkit for automating common DevOps tasks on `apt`-based Linux systems.

## Overview

The project provides a unified interface for:

- configuring `UFW`
- installing, enabling, and disabling `BBR`
- installing and removing `Docker`
- installing, activating, and removing `Fail2Ban`
- installing and removing `TrafficGuard`
- installing and removing `uv`

Supported workflows:

- interactive mode
- non-interactive CLI
- console logging and `app.log`

## Requirements

- Python `3.12+`
- Debian, Ubuntu, or another `apt`-based distribution
- `root` privileges for operations that change system state

## Running

```bash
sudo ./run.sh
sudo python3 main.py
```

`run.sh` bootstraps `uv` automatically. If `uv` is missing, the script installs `curl` when needed, runs the official installer, sources `"$HOME/.local/bin/env"`, creates owned symlinks in `/usr/local/bin` so `uv` is globally callable, runs `uv sync`, and then starts the app through `./.venv/bin/python3`.

### Non-interactive mode

Arguments:

- `--log-level {debug,info,warning,error}`
- `--install [codes...]`
- `--uninstall [codes...]`
- `--activate [codes...]`
- `--deactivate [codes...]`
- `--status [codes...]`
- `--info [codes...]`
- `--lang {ru,en}`
- `--all`

Examples:

```bash
sudo ./run.sh --install 1 2 3
sudo ./run.sh --uninstall 3 4
sudo ./run.sh --activate 1 2 4
sudo ./run.sh --status --all
sudo ./run.sh --info 1 4 6
sudo ./run.sh --lang en --status 1 4
sudo ./run.sh --log-level debug --install 2 4
```

Notes:

- use `--all` with one explicit non-interactive operation, for example `--status --all`
- the default interface language is `ru`; switch to English with `--lang en`
- activatable services are `UFW`, `BBR`, and `Fail2Ban`
- `Docker`, `TrafficGuard`, and `UV` support install/uninstall plus `status/info`

## Service codes

- `1=UFW`
- `2=BBR`
- `3=Docker`
- `4=Fail2Ban`
- `5=TrafficGuard`
- `6=UV`

## Services

### UFW

Installs, safely enables, resets, and removes the firewall.

### BBR

Prepares configuration, enables, and disables `TCP BBR congestion control`.

### Docker

Installs and fully removes `Docker Engine`.

### Fail2Ban

Installs, activates, and configures an SSH jail for brute-force protection.

### TrafficGuard

Provides broader protection against scanners and related network abuse.

### UV

Installs and removes the modern Python package manager `uv`.

- standard installation stays in `~/.local/bin`
- when running as `root` or via `sudo`, the project also creates owned symlinks in `/usr/local/bin` for global `uv`, `uvx`, and `uvw` access

## Logging

- console verbosity is controlled by `--log-level`
- detailed logs are written to `app.log` when available
- `DEBUG` is intended for diagnostics and internal telemetry
- `INFO` is intended for readable operator-facing output

## OS updates

The tool no longer performs an unconditional `apt update` on every start.

- `apt update` is skipped when the last successful package-list refresh is newer than `6` hours
- `apt upgrade` runs only when `apt list --upgradable` reports real packages to upgrade

## Development

Recommended options:

- local development with `.venv`
- container workflow via `Dockerfile` and `compose.yml`
- DevContainer via `.devcontainer/devcontainer.json`

If you want to use `uv` locally:

```bash
uv sync --group dev
```

## Testing

Locally:

```bash
./.venv/bin/pytest -q
./.venv/bin/pytest -q --cov=app --cov=main --cov-report=term-missing
```

In a container:

```bash
docker compose build test
docker compose run --rm test pytest -q --cov=app --cov=main --cov-report=term-missing
```

Latest full run:

- `399 passed`
- `6 skipped`
- coverage: `89%`
