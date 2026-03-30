# DevOps Automation Scripts

Этот документ фиксирует текущее устройство проекта `deb_scripts` и соглашения, которых нужно придерживаться при изменениях кода и документации.

## Обзор

`deb_scripts` — это набор Python-скриптов для автоматизации DevOps-задач в Linux-системах на базе `apt` (`Debian`, `Ubuntu` и производные).
Проект поддерживает интерактивный режим, неинтерактивный CLI и тестовый прогон в привилегированной контейнерной среде.

## Актуальная архитектура

- `main.py`:
  - проверяет запуск от `root`
  - один раз вызывает `update_os()`
  - переключает приложение между интерактивным и неинтерактивным режимом
  - преобразует верхнеуровневые ошибки в коды завершения через `run_cli()`
- `app/services/*`:
  - содержат всю операционную логику
  - логируют шаги, предупреждения и ошибки
  - используют единый публичный контракт `install()` / `uninstall()`
  - по возможности возвращают `bool`, чтобы CLI мог корректно формировать exit code
- `app/interfaces/cli/non_interactive.py`:
  - только маршрутизирует коды сервисов
  - не дублирует сервисные `INFO`-логи
  - опирается на единый API `install()` / `uninstall()`
- `app/interfaces/interactive/*`:
  - отвечают только за ввод, меню и информационные экраны
  - используют общий loop-based шаблон меню из `menu_utils.py`
  - не должны строить рекурсивную навигацию
- `app/utils/*`:
  - содержат общий код без дублирования бизнес-логики сервисов

## Инструкции для AI

1. **Безопасность**:
   - все изменения должны быть идемпотентными
   - перед системными изменениями учитывай, что приложение должно работать только от `root`
   - не ломай безопасный baseline для `UFW`: `deny incoming`, `allow outgoing`, SSH-разрешение
2. **Стиль кода**:
   - типизация обязательна
   - следуй PEP 8 (макс. длина строки `99`)
   - имена: `snake_case` для функций и переменных, `PascalCase` для классов
3. **Логирование**:
   - используй `app.utils.logger`
   - сервисы логируют рабочие шаги и ошибки
   - интерфейсы не должны дублировать сервисные логи об успехе установки или удаления
4. **Обработка ошибок**:
   - перехватывай конкретные исключения
   - логируй контекст
   - возвращай `False`, если операция не завершилась успешно
5. **Формат изменений**:
   - при добавлении новой логики сначала проверь существующие helper'ы
   - не дублируй меню, статусы и CLI-маршрутизацию вручную, если это уже вынесено в общие модули
6. **Тестирование**:
   - основной сценарий запуска тестов — контейнер из `compose.yml`
   - локальный прогон допустим для unit/integration
   - для полного прогона и покрытия используй `pytest` и `pytest-cov`
7. **Интерактивный режим**:
   - меню должны использовать единый формат и общий цикл из `menu_utils.py`
   - главное меню обязано показывать текущий статус сервисов
   - сервисные подменю обязаны иметь `00` для информации и `0` для возврата назад
   - статус должен выводиться как короткий inline-индикатор `🟢` / `🔴`

## Соглашения по коду

### Сервисы

- Все сервисы должны предоставлять:
  - `install()`
  - `uninstall()`
  - `is_installed()`
  - `get_status()`
- Там, где важно не только наличие пакета, но и рабочее состояние, добавляй `is_active()`.
- Исторические методы вроде `install_docker()` или `enable_bbr()` можно сохранять как внутренние/совместимые точки входа, но внешний интерфейс должен оставаться единообразным.

### Неинтерактивный CLI

- Коды сервисов централизованы в `app/interfaces/cli/non_interactive.py`
- Текущая карта кодов:
  - `1=UFW`
  - `2=BBR`
  - `3=Docker`
  - `4=Fail2Ban`
  - `5=TrafficGuard`
  - `6=UV`
- Если хотя бы одна операция завершилась неуспешно, CLI должен завершаться с ненулевым кодом.

### Интерактивные меню

- Используй `MenuItem`, `run_menu_loop()` и связанные helper'ы из `app/interfaces/interactive/menu_utils.py`.
- Для типовых сервисных подменю используй `build_standard_service_menu_items(...)`.
- Не возвращайся в главное меню через повторный вызов `run_interactive_script()`.
- Для статусов используй `status_utils.py`, а не строковые шаблоны, размазанные по файлам.

### Обновление системы

- `update_os()` должен вызываться только один раз при старте приложения из `main.py`.
- Не добавляй `apt update/upgrade` внутрь отдельных `install()`-методов сервисов.

## Добавление нового сервиса

1. Создай `app/services/new_service.py` с классом `NewService`.
2. Реализуй единый контракт:
   - `install()`
   - `uninstall()`
   - `is_installed()`
   - `get_status()`
   - при необходимости `is_active()`
3. Создай `app/interfaces/interactive/new_service.py` с меню на базе `menu_utils.py`.
4. Добавь сервис в:
   - `app/interfaces/interactive/run.py`
   - `app/interfaces/cli/non_interactive.py`
   - `app/utils/args_utils.py` в help для `--install/--uninstall`
5. Добавь тесты:
   - `tests/unit/test_new_service.py`
   - при необходимости `tests/integration/test_new_service_integration.py`
   - при необходимости `tests/system/test_new_service_system.py`
6. Обнови документацию:
   - `README.md`
   - `tests/README.md`, если меняется тестовая стратегия
   - этот файл

## Тестирование

### Предпочтительный прогон

```bash
docker compose build test
docker compose run --rm test pytest -q --cov=app --cov=main --cov-report=term-missing
```

### Локальный прогон

```bash
uv sync --group dev
uv run pytest -q
uv run pytest -q --cov=app --cov=main --cov-report=term-missing
```

### По категориям

```bash
docker compose run --rm test pytest -m unit -q
docker compose run --rm test pytest -m integration -q
docker compose run --rm test pytest -m system -q -rs
```

### Текущее состояние тестов

На момент последнего полного прогона:

- `340 passed, 7 skipped`
- общее покрытие: `92%`

Системные skip'ы допустимы, если среда не даёт `sysctl`, `systemd` или привилегии для отдельных smoke-сценариев.

## Важные файлы

- `main.py` — точка входа, запуск обновления системы, выбор режима, exit codes
- `run.sh` — тонкая обёртка над `python3 main.py`
- `app/interfaces/interactive/menu_utils.py` — общий шаблон интерактивных меню
- `app/interfaces/interactive/status_utils.py` — helper'ы для короткого отображения статусов
- `app/interfaces/cli/non_interactive.py` — маршрутизация `--install/--uninstall`
- `app/utils/args_utils.py` — аргументы CLI и тестовый `app_args`
- `app/utils/update_utils.py` — `apt update` / `apt upgrade`
- `tests/conftest.py` — фикстуры и регистрация pytest-маркеров
- `tests/README.md` — описание структуры тестов
- `.devcontainer/devcontainer.json` — DevContainer на базе `Dockerfile`
- `compose.yml` — контейнерный сценарий для тестов

## Использование

```bash
git clone https://github.com/thegrayfoxxx/deb_scripts.git
cd deb_scripts

# Пользовательский запуск
sudo ./run.sh
sudo python3 main.py --mode dev

# Разработка
uv sync --group dev
uv run pytest -q
```
