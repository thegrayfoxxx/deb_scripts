# 🐍 DevOps Automation Scripts

![GitHub](https://img.shields.io/github/license/thegrayfoxxx/deb_scripts?color=blue)
![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)
![Debian](https://img.shields.io/badge/Debian-Bookworm-blue?logo=debian)

Python toolkit for automating common DevOps tasks on `apt`-based Linux systems.

## What it does

- manages `UFW`
- enables and disables `BBR`
- installs and removes `Docker`
- installs and configures `Fail2Ban`
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

## CLI example

```bash
sudo ./run.sh --install 1 2 3
sudo ./run.sh --uninstall 3 4
sudo ./run.sh --log-level debug --install 2 4
```

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

## Testing

```bash
./.venv/bin/pytest -q
./.venv/bin/pytest -q --cov=app --cov=main --cov-report=term-missing
```

Latest full run:

- `345 passed`
- `6 skipped`
- coverage: `92%`

## License

MIT License © 2025 thegrayfoxxx
