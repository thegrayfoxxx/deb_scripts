# Документация deb_scripts

`deb_scripts` — набор Python-скриптов для автоматизации типовых DevOps-задач в Linux-окружении на базе `apt`.

## Обзор

Проект предоставляет единый интерфейс для:

- настройки `UFW`
- установки, включения и отключения `BBR`
- установки и удаления `Docker`
- установки, активации и удаления `Fail2Ban`
- установки и удаления `TrafficGuard`
- установки и удаления `uv`

Поддерживаются:

- интерактивный режим
- неинтерактивный CLI
- логирование в консоль и `app.log`

## Требования

- Python `3.12+`
- Debian, Ubuntu или совместимый `apt`-дистрибутив
- запуск от `root` для операций, меняющих системное состояние

## Запуск

```bash
sudo ./run.sh
sudo python3 main.py
```

`run.sh` автоматически подготавливает `uv`. Если `uv` отсутствует, скрипт при необходимости устанавливает `curl`, запускает официальный installer, делает `source "$HOME/.local/bin/env"`, создаёт принадлежащие проекту симлинки в `/usr/local/bin` для глобального вызова `uv`, выполняет `uv sync`, а затем запускает приложение через `./.venv/bin/python3`.

### Неинтерактивный режим

Аргументы:

- `--log-level {debug,info,warning,error}`
- `--install [codes...]`
- `--uninstall [codes...]`
- `--activate [codes...]`
- `--deactivate [codes...]`
- `--status [codes...]`
- `--info [codes...]`
- `--lang {ru,en}`
- `--all`

Примеры:

```bash
sudo ./run.sh --install 1 2 3
sudo ./run.sh --uninstall 3 4
sudo ./run.sh --activate 1 2 4
sudo ./run.sh --status --all
sudo ./run.sh --info 1 4 6
sudo ./run.sh --lang en --status 1 4
sudo ./run.sh --log-level debug --install 2 4
```

Примечания:

- `--all` применяется к одной явно указанной non-interactive операции, например `--status --all`
- язык интерфейса по умолчанию `ru`, для английского используйте `--lang en`
- сервисы с отдельной активацией: `UFW`, `BBR`, `Fail2Ban`
- `Docker`, `TrafficGuard` и `UV` поддерживают установку/удаление, а также `status/info`

## Коды сервисов

- `1=UFW`
- `2=BBR`
- `3=Docker`
- `4=Fail2Ban`
- `5=TrafficGuard`
- `6=UV`

## Сервисы

### UFW

Установка, безопасное включение, сброс и удаление межсетевого экрана.

### BBR

Подготовка конфигурации, включение и отключение `TCP BBR congestion control`.

### Docker

Установка и полное удаление `Docker Engine`.

### Fail2Ban

Установка, активация и настройка SSH jail для защиты от brute-force.

### TrafficGuard

Комплексная защита от сетевых сканеров и связанных атак.

### UV

Установка и удаление современного Python package manager `uv`.

- стандартная установка остаётся в `~/.local/bin`
- при запуске от `root` или через `sudo` проект дополнительно создаёт собственные симлинки в `/usr/local/bin` для глобального доступа к `uv`, `uvx` и `uvw`

## Логирование

- консольный уровень задаётся через `--log-level`
- подробные логи пишутся в `app.log`, если файл доступен
- `DEBUG` предназначен для диагностики и внутренней телеметрии
- `INFO` предназначен для понятного операторского вывода

## Обновление ОС

При старте приложение не делает безусловный `apt update`.

- `apt update` пропускается, если последний успешный update был меньше `6` часов назад
- `apt upgrade` выполняется только если `apt list --upgradable` показывает реальные пакеты для обновления

## Разработка

Рекомендуемые варианты:

- локальная разработка с `.venv`
- контейнер из `Dockerfile` и `compose.yml`
- DevContainer из `.devcontainer/devcontainer.json`

Если используешь `uv` локально:

```bash
uv sync --group dev
```

## Тестирование

Локально:

```bash
./.venv/bin/pytest -q
./.venv/bin/pytest -q --cov=app --cov=main --cov-report=term-missing
```

В контейнере:

```bash
docker compose build test
docker compose run --rm test pytest -q --cov=app --cov=main --cov-report=term-missing
```

Последний полный прогон:

- `399 passed`
- `6 skipped`
- покрытие: `89%`
