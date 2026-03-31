# 🐍 DevOps Automation Scripts

![License](https://img.shields.io/github/license/thegrayfoxxx/deb_scripts?color=2d6a4f)
![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Linux-Debian%20%7C%20Ubuntu-A81D33?logo=debian&logoColor=white)
![Release](https://img.shields.io/github/v/tag/thegrayfoxxx/deb_scripts?sort=semver&label=release)
![Coverage](https://img.shields.io/badge/coverage-89%25-0a7f5a)

Python toolkit for automating common DevOps tasks on `apt`-based Linux systems.

Supported services: `UFW`, `BBR`, `Docker`, `Fail2Ban`, `TrafficGuard`, `uv`.

## 🚀 Run

```bash
git clone https://github.com/thegrayfoxxx/deb_scripts.git
cd deb_scripts
sudo ./run.sh
```

If you are already running as `root`, use:

```bash
./run.sh
```

Requirements: `Python 3.12+`, Debian/Ubuntu or another `apt`-based distribution, and `root` privileges for system-changing operations.

## 💻 CLI

```bash
sudo ./run.sh --status --all
sudo ./run.sh --info 1 4 6
```

## 📚 Documentation

- [Русская документация](docs/ru/README.md)
- [English documentation](docs/en/README.md)

The language-specific docs contain setup, usage, service codes, logging, development, and testing details.

## 🏷️ Releases

Pushing a Git tag that matches `v*`, for example `v2.1.1`, triggers a GitHub Actions workflow that creates a GitHub Release with generated notes.

## 📄 License

MIT License © 2025 thegrayfoxxx
