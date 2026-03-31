# 🐍 DevOps Automation Scripts

![GitHub](https://img.shields.io/github/license/thegrayfoxxx/deb_scripts?color=blue)
![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)
![Debian](https://img.shields.io/badge/Debian-Bookworm-blue?logo=debian)

Python toolkit for automating common DevOps tasks on `apt`-based Linux systems.

## What it does

- manages `UFW`
- installs, enables, and disables `BBR`
- installs and removes `Docker`
- installs, activates, and removes `Fail2Ban`
- installs and removes `TrafficGuard`
- installs and removes `uv`

The project supports both interactive mode and non-interactive CLI automation.

## Quick start

```bash
git clone https://github.com/thegrayfoxxx/deb_scripts.git
cd deb_scripts
sudo ./run.sh
```

Requirements:

- Python `3.12+`
- Debian, Ubuntu, or another `apt`-based distribution
- `root` privileges for system-changing operations

`run.sh` checks for `uv` on startup. If `uv` is missing, the script installs `curl` when needed, runs the official `uv` installer, sources `"$HOME/.local/bin/env"`, publishes owned symlinks in `/usr/local/bin` for global `uv` access, runs `uv sync`, and then starts the app through `./.venv/bin/python3`.

## CLI example

```bash
sudo ./run.sh --install 1 2 3
sudo ./run.sh --uninstall 3 4
sudo ./run.sh --activate 1 2 4
sudo ./run.sh --status --all
sudo ./run.sh --info 1 4 6
sudo ./run.sh --lang en --status 1 4
sudo ./run.sh --log-level debug --install 2 4
```

Supported non-interactive flags:

- `--install [codes...]`
- `--uninstall [codes...]`
- `--activate [codes...]`
- `--deactivate [codes...]`
- `--status [codes...]`
- `--info [codes...]`
- `--lang {ru,en}`
- `--all`

Notes:

- use `--all` with one non-interactive operation, for example `--status --all`
- the default interface language is `ru`; switch to English with `--lang en`
- activatable services are `UFW`, `BBR`, and `Fail2Ban`
- `TrafficGuard`, `Docker`, and `UV` support install/uninstall plus status/info

## Update behavior

On startup the tool checks whether the package index is still fresh.

- `apt update` is skipped if the last successful update is newer than `6` hours
- `apt upgrade` runs only when `apt list --upgradable` reports real packages to upgrade

Service codes:

- `1=UFW`
- `2=BBR`
- `3=Docker`
- `4=Fail2Ban`
- `5=TrafficGuard`
- `6=UV`

## Documentation

- [Русская документация](docs/ru/README.md)
- [English documentation](docs/en/README.md)

The language-specific docs contain setup, usage, logging, development, and testing details.

## Releases

Pushing a Git tag that matches `v*`, for example `v2.1.1`, triggers a GitHub Actions workflow that creates a GitHub Release with generated notes.

## Testing

```bash
./.venv/bin/pytest -q
./.venv/bin/pytest -q --cov=app --cov=main --cov-report=term-missing
```

Latest full run:

- `399 passed`
- `6 skipped`
- coverage: `89%`

## License

MIT License © 2025 thegrayfoxxx
