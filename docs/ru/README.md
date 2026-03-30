# Документация deb_scripts

`deb_scripts` — набор Python-скриптов для автоматизации типовых DevOps-задач в Linux-окружении на базе `apt`.

## Обзор

Проект предоставляет единый интерфейс для:

- настройки `UFW`
- включения `BBR`
- установки и удаления `Docker`
- установки и настройки `Fail2Ban`
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

### Неинтерактивный режим

Аргументы:

- `--log-level {debug,info,warning,error}`
- `--install <codes...>`
- `--uninstall <codes...>`

Примеры:

```bash
sudo ./run.sh --install 1 2 3
sudo ./run.sh --uninstall 3 4
sudo ./run.sh --log-level debug --install 2 4
```

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

Включение и отключение `TCP BBR congestion control`.

### Docker

Установка и полное удаление `Docker Engine`.

### Fail2Ban

Установка и настройка SSH jail для защиты от brute-force.

### TrafficGuard

Комплексная защита от сетевых сканеров и связанных атак.

### UV

Установка и удаление современного Python package manager `uv`.

## Логирование

- консольный уровень задаётся через `--log-level`
- подробные логи пишутся в `app.log`, если файл доступен
- `DEBUG` предназначен для диагностики и внутренней телеметрии
- `INFO` предназначен для понятного операторского вывода

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

- `345 passed`
- `6 skipped`
- покрытие: `92%`
