# 🐍 DevOps Automation Scripts

![GitHub](https://img.shields.io/github/license/thegrayfoxxx/deb_scripts?color=blue)
![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)
![Debian](https://img.shields.io/badge/Debian-Bookworm-blue?logo=debian)

Набор Python-скриптов для автоматизации типовых DevOps-задач в Linux-окружении на базе `apt`.
Проект объединяет настройку сети, базовую защиту сервера и установку сопутствующих инструментов через единый CLI.

## 🚀 Возможности

- Поддержка Debian, Ubuntu и производных дистрибутивов
- Интерактивный режим с единым loop-based меню
- Неинтерактивный режим для автоматизации через аргументы CLI
- Единый контракт сервисов: `install()`, `uninstall()`, `is_installed()`, `get_status()`
- Статусы сервисов прямо в главном меню и подменю (`🟢` / `🔴`)
- Логирование в консоль и файл `app.log`
- Покрытие тестами: `92%` на момент последнего прогона

## 📦 Сервисы

| Код | Сервис | Назначение |
| --- | --- | --- |
| `1` | UFW | Установка, безопасное включение, сброс и удаление межсетевого экрана |
| `2` | BBR | Включение и отключение TCP BBR congestion control |
| `3` | Docker | Установка и полное удаление Docker Engine |
| `4` | Fail2Ban | Установка и настройка jail для `sshd` |
| `5` | TrafficGuard | Установка и удаление комплексной защиты от сетевых сканеров |
| `6` | UV | Установка и удаление менеджера пакетов `uv` |

## 📥 Установка

```bash
git clone https://github.com/thegrayfoxxx/deb_scripts.git
cd deb_scripts
```

### Требования

- Python `3.12+`
- POSIX-совместимая оболочка (`bash`/`zsh`)
- Права `root` для системных изменений

Runtime-часть проекта использует стандартную библиотеку Python. Для разработки и тестов используются `pytest` и `pytest-cov`.

## 👥 Использование

### Запуск

Все основные операции изменяют системное состояние, поэтому запускать их нужно с повышенными правами:

```bash
sudo ./run.sh
sudo python3 main.py
```

`run.sh` является простой обёрткой вокруг `python3 main.py`.

При старте приложения один раз выполняется обновление системы:

1. `apt update -y`
2. `apt upgrade -y`

Этот шаг вызывается только из `main.py`, а не отдельно в каждом сервисе.

### Интерактивный режим

Интерактивное меню запускается по умолчанию. Главное меню показывает текущий статус каждого сервиса:

```text
1 - 🔥 UFW - uncomplicated firewall (межсетевой экран) (🟢 включен / 🔴 не установлен / 🔴 выключен)
2 - 🌐 BBR (TCP Congestion Control) - ускорение сети (🟢 включен / 🔴 выключен)
3 - 🐳 Docker - установка контейнеризации (🟢 установлен / 🔴 не установлен)
4 - 🛡️ Fail2Ban - защита от атак (🟢 активен / 🔴 не установлен / 🔴 не активен)
5 - ⚔️ TrafficGuard - комплексная защита (🟢 активен / 🔴 не установлен / 🔴 не активен)
6 - 🐍 UV - менеджер пакетов Python (🟢 установлен / 🔴 не установлен)
00 - ℹ️ Информация о программе
0 - ❌ Выход
```

Особенности интерактивного режима:

- у каждого сервиса есть отдельное подменю
- в подменю есть пункт `Показать статус`
- `00` показывает информационный экран
- `0` возвращает назад, не создавая вложенную рекурсию меню

### Неинтерактивный режим

Поддерживаемые аргументы:

- `--mode {dev,prod}`: `dev` включает `DEBUG`-логирование
- `--install <codes...>`: установка одного или нескольких сервисов
- `--uninstall <codes...>`: удаление одного или нескольких сервисов

Примеры:

```bash
# Установить UFW, BBR и Docker
sudo ./run.sh --install 1 2 3

# Удалить Docker и Fail2Ban
sudo ./run.sh --uninstall 3 4

# Смешанный сценарий
sudo ./run.sh --install 1 6 --uninstall 3

# Подробное логирование
sudo ./run.sh --mode dev --install 2 4
```

Коды сервисов:

- `1=UFW`
- `2=BBR`
- `3=Docker`
- `4=Fail2Ban`
- `5=TrafficGuard`
- `6=UV`

Неинтерактивный CLI использует только единый API сервисов `install()` / `uninstall()` и возвращает ненулевой код завершения, если хотя бы одна операция завершилась неуспешно.

## 📂 Структура проекта

```text
deb_scripts/
├── app/
│   ├── interfaces/
│   │   ├── cli/
│   │   │   └── non_interactive.py
│   │   └── interactive/
│   │       ├── run.py
│   │       ├── menu_utils.py
│   │       ├── status_utils.py
│   │       ├── ufw.py
│   │       ├── bbr.py
│   │       ├── docker.py
│   │       ├── fail2ban.py
│   │       ├── traffic_guard.py
│   │       └── uv.py
│   ├── services/
│   │   ├── ufw.py
│   │   ├── bbr.py
│   │   ├── docker.py
│   │   ├── fail2ban.py
│   │   ├── traffic_guard.py
│   │   └── uv.py
│   └── utils/
│       ├── args_utils.py
│       ├── logger.py
│       ├── permission_utils.py
│       ├── subprocess_utils.py
│       └── update_utils.py
├── main.py
├── run.sh
├── Dockerfile
├── compose.yml
├── pyproject.toml
└── tests/
    ├── unit/
    ├── integration/
    ├── system/
    ├── conftest.py
    └── README.md
```

## 📝 Логирование

Логи пишутся:

- в консоль
- в файл `app.log`, если он доступен на запись

В `dev`-режиме включается уровень `DEBUG`, в `prod`-режиме используется `INFO`.

Если файловый лог недоступен, приложение продолжает работать с консольным логированием и не падает на импорте модулей.

Пример записи:

```text
2026-03-30 05:53:55 - app.services.traffic_guard - INFO - ⬇️ Загрузка официального установочного скрипта TrafficGuard...
```

## ⚠️ Безопасность

Скрипты выполняют потенциально опасные системные изменения:

- устанавливают и удаляют пакеты
- меняют конфигурацию в `/etc`
- управляют службами и сетевыми правилами
- вызывают `sysctl`, `iptables`, `ufw` и другие системные утилиты

Дополнительно:

- `Docker`, `UV` и `TrafficGuard` используют внешние установочные скрипты
- часть системных тестов зависит от особенностей ядра, `systemd` и доступных capability
- перед запуском на реальном сервере стоит проверить сценарий в изолированной среде

## 👨‍💻 Разработка

### Рекомендуемая среда

Основной сценарий разработки и тестирования:

- DevContainer из `.devcontainer/devcontainer.json`
- или контейнер из `Dockerfile` / `compose.yml`

Контейнер запускается в привилегированном режиме, потому что часть кода работает с сетевыми настройками, `sysctl` и системными службами.

### Локальная подготовка

```bash
uv sync --group dev
```

### Тестирование

Предпочтительный вариант:

```bash
docker compose build test
docker compose run --rm test pytest -q --cov=app --cov=main --cov-report=term-missing
```

Локальный запуск:

```bash
uv run pytest -q
uv run pytest -q --cov=app --cov=main --cov-report=term-missing
```

Запуск отдельных групп тестов:

```bash
docker compose run --rm test pytest -m unit -q
docker compose run --rm test pytest -m integration -q
docker compose run --rm test pytest -m system -q -rs
```

На момент последнего полного прогона:

- `340 passed, 7 skipped`
- общее покрытие: `92%`

Подробнее см. [tests/README.md](tests/README.md) и [tests/system/README.md](tests/system/README.md).

## 🤝 Вклад

1. Сделайте fork репозитория.
2. Создайте ветку: `git checkout -b feature/amazing-feature`
3. Внесите изменения и добавьте тесты при необходимости.
4. Зафиксируйте результат: `git commit -m "Add amazing feature"`
5. Откройте Pull Request.

## 📜 Лицензия

MIT License © 2025 thegrayfoxxx
