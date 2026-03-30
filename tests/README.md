# Тесты проекта deb_scripts

Каталог `tests/` содержит юнит-, интеграционные и системные тесты для сервисов, CLI, интерактивного режима и общих утилит проекта.

## Структура

- `unit/` — изолированные тесты сервисов, интерфейсов и `utils`
- `integration/` — проверка взаимодействия между сервисами, интерфейсами и общими утилитами
- `system/` — сценарии, которым требуется реальная системная среда
- `conftest.py` — общие фикстуры, регистрация pytest-маркеров и базовая настройка тестов

Примеры покрываемых областей:

- `tests/unit/test_ufw_service.py`
- `tests/unit/test_main.py`
- `tests/unit/test_interactive_status_menus.py`
- `tests/integration/test_interactive_interfaces.py`
- `tests/integration/test_integration.py`
- `tests/system/test_system_commands.py`

## Как запускать

Предпочтительная среда запуска — привилегированный контейнер из `compose.yml`.

### Все тесты

```bash
docker compose build test
docker compose run --rm test pytest -q
```

### Все тесты с покрытием

```bash
docker compose run --rm test pytest -q --cov=app --cov=main --cov-report=term-missing
```

### По категориям

```bash
docker compose run --rm test pytest -m unit -q
docker compose run --rm test pytest -m integration -q
docker compose run --rm test pytest -m system -q -rs
docker compose run --rm test pytest -m "system and slow" -q -rs
```

### Локальный запуск

```bash
uv sync --group dev
uv run pytest -q
uv run pytest -q --cov=app --cov=main --cov-report=term-missing
```

Для системных сценариев локальный запуск не рекомендуется: часть тестов ожидает Linux-окружение с доступом к системным утилитам, `sysctl`, сетевым настройкам и иногда к привилегированным capability.

## Маркеры

В проекте используются маркеры:

- `unit`
- `integration`
- `system`
- `slow`

Маркеры регистрируются в `tests/conftest.py`. Если тест не отмечен как `integration` или `system`, ему автоматически добавляется `unit`.

## Что проверяют тесты

- корректность CLI-маршрутизации и exit code
- единый контракт сервисов `install()` / `uninstall()`
- поведение сервисов в успешных и ошибочных сценариях
- работу интерактивных меню, включая статусы и loop-based навигацию
- вызовы системных команд через общий wrapper
- согласованность интерфейсов между `services`, `interfaces` и `utils`
- работу в изолированной системной среде для наиболее рискованных операций

## Текущее состояние

На момент последнего полного прогона:

- `340 passed, 7 skipped`
- общее покрытие кода: `92%`

Покрытие снимается через `pytest-cov` и включает:

- `app`
- `main.py`

## Замечания

- Системные тесты предназначены для контейнера с `privileged: true`
- Некоторые системные тесты могут быть `skipped`, если в среде недоступны `sysctl`, отдельные capability или часть сетевой инфраструктуры
- Многие unit/integration тесты используют `unittest.mock`, чтобы не изменять реальную систему
- При отладке проблем сначала запускайте `unit`, затем `integration`, и только после этого `system`
