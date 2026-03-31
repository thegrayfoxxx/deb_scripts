# 📚 deb_scripts Documentation

`deb_scripts` is a Python toolkit for automating common DevOps tasks on `apt`-based Linux systems.

## ✨ What the project does

The project provides a unified interface for:

- configuring `UFW`
- installing, enabling, and disabling `BBR`
- installing and removing `Docker`
- installing, activating, and removing `Fail2Ban`
- installing and removing `TrafficGuard`
- installing and removing `uv`

Supported workflows:

- interactive menu mode
- non-interactive CLI mode
- operator-facing console output
- logging to `app.log`

Current project version: `2.1.3`.

## 🧰 System requirements

- `Python 3.12+`
- preinstalled `git`
- `Debian 12+` or `Ubuntu 22.04+`
- access to `apt`
- `root` privileges for operations that change system state

Minimum supported distributions:

- `Debian 12+`
- `Ubuntu 22.04+`

The project is designed to run as `root`. For a regular user, the normal launch command is `sudo ./run.sh`.

## 🚀 Installation and first run

### Recommended path

```bash
git clone https://github.com/thegrayfoxxx/deb_scripts.git
cd deb_scripts
sudo ./run.sh
```

`git` should already be installed on the system, since the normal installation flow starts with `git clone`.

If the current user is already `root`, run it without `sudo`:

```bash
./run.sh
```

### What `run.sh` does

`run.sh` is the main project launcher. It is the recommended entrypoint for normal operation.

At startup, the script:

1. resolves the correct `HOME` for the effective user
2. tries to source `"$HOME/.local/bin/env"`
3. checks whether `uv` is available
4. installs `curl` if needed
5. installs `uv` with the official command `curl -LsSf https://astral.sh/uv/install.sh | sh`
6. sources `"$HOME/.local/bin/env"` again
7. creates project-owned symlinks in `/usr/local/bin` for global `uv`, `uvx`, and `uvw` access
8. runs `uv sync`
9. starts the app through `./.venv/bin/python3 ./main.py`

This flow exists so the project can:

- keep the default `uv` installation in `~/.local/bin`
- still make `uv` globally callable when launched as `root` or via `sudo`
- avoid requiring manual `.venv` preparation

### Do you need to install dependencies manually

No. In the normal runtime flow, `run.sh` handles bootstrap automatically:

- it installs `uv` if missing
- it syncs the project environment through `uv sync`
- it launches `main.py` from the local `.venv`

Manual `uv` usage is mainly for development or debugging.

## 🔀 Operating modes

The project supports two modes:

- interactive menu mode
- non-interactive CLI mode

If `run.sh` is called without CLI arguments, the interactive menu is started.

If arguments such as `--install`, `--status`, or `--info` are passed, the application switches to non-interactive mode.

## 🖥️ Interactive mode

Normal launch:

```bash
sudo ./run.sh
```

If the current user is already `root`:

```bash
./run.sh
```

After startup, the main menu shows the supported services and their current status.

The main menu uses these service codes:

- `1=UFW`
- `2=BBR`
- `3=Docker`
- `4=Fail2Ban`
- `5=TrafficGuard`
- `6=UV`

Each service has its own submenu for install, uninstall, status, and info operations. Activatable services also expose activate and deactivate actions.

## 💻 Non-interactive CLI

### Supported arguments

- `--log-level {debug,info,warning,error}`
- `--install [codes...]`
- `--uninstall [codes...]`
- `--activate [codes...]`
- `--deactivate [codes...]`
- `--status [codes...]`
- `--info [codes...]`
- `--lang {ru,en}`
- `--all`

### Usage rules

- `--all` applies to one explicitly selected operation only, for example `--status --all`
- do not pass service codes and `--all` together for the same operation
- if an operation is given without service codes, you must either pass codes or use `--all`
- the default UI language is `ru`; use `--lang en` for English output

### Examples

Run these examples with `sudo` as a regular user, or drop `sudo` if the current user is already `root`.

```bash
sudo ./run.sh --status --all
sudo ./run.sh --install 1 2 3
sudo ./run.sh --activate 1 2 4
sudo ./run.sh --info 1 4 6
sudo ./run.sh --lang en --status 1 4
sudo ./run.sh --log-level debug --uninstall 3
```

## 🔢 Service codes

- `1=UFW`
- `2=BBR`
- `3=Docker`
- `4=Fail2Ban`
- `5=TrafficGuard`
- `6=UV`

## 🧩 Service behavior

### UFW

- installs and configures `ufw`
- keeps the safe baseline: `deny incoming`, `allow outgoing`
- preserves SSH access
- supports separate activate and deactivate actions

### BBR

- configures kernel settings for `TCP BBR`
- checks installed state
- supports separate activate and deactivate actions

### Docker

- installs `Docker Engine`
- fully removes Docker components
- provides status and info output

### Fail2Ban

- installs `fail2ban`
- configures and activates SSH protection
- supports separate activate and deactivate actions

### TrafficGuard

- installs and removes broader network protection
- provides status and info output

### UV

- installs the modern Python package manager `uv`
- removes `uv` and related data
- reports status, version, and PATH visibility

The `uv` flow follows this model:

- the default installation remains in `~/.local/bin`
- when the project runs as `root` or via `sudo`, it also creates project-owned symlinks in `/usr/local/bin`
- this preserves the default `uv` install flow while also making `uv`, `uvx`, and `uvw` globally callable

## 📝 Logging

The project writes operator-facing messages to the console and, when available, to `app.log`.

Levels:

- `debug` for detailed diagnostics and internal telemetry
- `info` for normal operator-facing output
- `warning` for degraded but non-fatal situations
- `error` for operation failures

Example:

```bash
sudo ./run.sh --log-level debug --status 6
```

## 🔄 OS update behavior

The application does not perform an unconditional `apt update` on every start.

Current logic:

- `apt update` is skipped if the last successful refresh is newer than `6` hours
- `apt upgrade` runs only when `apt list --upgradable` reports real packages to upgrade

This behavior is centralized in the application entrypoint instead of being duplicated across services.

## 🛠️ Development

### Local `uv` workflow

If you are developing locally and want to prepare the environment manually:

```bash
uv sync --group dev
```

After that, you can run tests directly:

```bash
./.venv/bin/pytest -q
```

### Container workflow

The repository includes:

- `Dockerfile`
- `compose.yml`

For containerized test execution:

```bash
docker compose build test
docker compose run --rm test pytest -q --cov=app --cov=main --cov-report=term-missing
```

### Project layout

- `run.sh` is the main launcher and environment bootstrap
- `main.py` is the Python entrypoint
- `app/services/` contains service business logic
- `app/interfaces/cli/` contains the non-interactive CLI layer
- `app/interfaces/menu/` contains interactive menus
- `app/bootstrap/` contains args, logging, preflight checks, and OS update logic
- `app/core/` contains shared helpers and the service registry
- `app/i18n/` contains localization
- `tests/` contains unit, integration, and system tests

## ✅ Testing

### Local

```bash
./.venv/bin/pytest -q
./.venv/bin/pytest -q tests/unit
./.venv/bin/pytest -q tests/integration
./.venv/bin/pytest -q --cov=app --cov=main --cov-report=term-missing
```

### In a container

```bash
docker compose build test
docker compose run --rm test pytest -q
docker compose run --rm test pytest -q --cov=app --cov=main --cov-report=term-missing
```

Latest full run:

- `399 passed`
- `6 skipped`
- coverage: `89%`

## 🏷️ Releases

The project version is stored in `pyproject.toml`.

If a change warrants a release:

1. update the version with `uv version --bump patch|minor|major`
2. create a matching git tag in the format `vX.Y.Z`
3. push the branch
4. push the tag

Example:

```bash
uv version --bump patch
git tag v2.1.4
git push origin master
git push origin v2.1.4
```

Pushing a tag that matches `v*` triggers the GitHub Actions workflow that creates a GitHub Release with generated notes.

## 🆘 Common issues

### `uv` is installed but `sudo uv` still does not work

Make sure the launcher has already run and created the symlinks in `/usr/local/bin`. The supported bootstrap path is launch through `run.sh`.

### The application does not start without `sudo`

That is expected. The project is designed to run as `root` because it manages system packages, firewall rules, sysctl settings, and services.

### Should you run `python3 main.py` directly

Not for normal operation. The recommended entrypoint is `run.sh` because it prepares `uv`, `.venv`, and the runtime environment first.
