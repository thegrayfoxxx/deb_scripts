# deb_scripts Documentation

`deb_scripts` is a Python-based toolkit for automating common DevOps tasks on `apt`-based Linux systems.

## Overview

The project provides a unified interface for:

- configuring `UFW`
- enabling `BBR`
- installing and removing `Docker`
- installing and configuring `Fail2Ban`
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

### Non-interactive mode

Arguments:

- `--log-level {debug,info,warning,error}`
- `--install <codes...>`
- `--uninstall <codes...>`

Examples:

```bash
sudo ./run.sh --install 1 2 3
sudo ./run.sh --uninstall 3 4
sudo ./run.sh --log-level debug --install 2 4
```

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

Enables and disables `TCP BBR congestion control`.

### Docker

Installs and fully removes `Docker Engine`.

### Fail2Ban

Installs and configures an SSH jail for brute-force protection.

### TrafficGuard

Provides broader protection against scanners and related network abuse.

### UV

Installs and removes the modern Python package manager `uv`.

## Logging

- console verbosity is controlled by `--log-level`
- detailed logs are written to `app.log` when available
- `DEBUG` is intended for diagnostics and internal telemetry
- `INFO` is intended for readable operator-facing output

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

- `345 passed`
- `6 skipped`
- coverage: `92%`
