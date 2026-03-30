# Утилиты проекта deb_scripts

Каталог `app/utils/` содержит общие модули, которые используются сервисами и интерфейсами CLI.

## Состав

- `args_utils.py` — разбор аргументов командной строки
- `logger.py` — настройка логирования в консоль и файл
- `permission_utils.py` — проверка запуска от `root`
- `subprocess_utils.py` — единая обёртка над `subprocess.run`
- `update_utils.py` — обновление системы через `apt`

## logger.py

`get_logger(name)` возвращает настроенный `logging.Logger`.

Особенности:

- пишет в `stdout`
- пытается писать в файл `app.log`
- использует `DEBUG` в режиме `--mode dev`
- использует `INFO` в режиме `prod`
- не должен падать на импорте, если `app.log` недоступен на запись

## subprocess_utils.py

`run(command, check=True, **kwargs)` запускает системную команду через `subprocess.run`.

Базовое поведение:

- `text=True`
- `capture_output=True`

Поведение по ошибкам:

- при `check=True` пробрасывает `CalledProcessError`
- при `check=False` возвращает объект результата даже для неуспешного кода возврата

Дополнительно:

- `is_command_available(cmd)` используется для быстрой проверки наличия команды

## update_utils.py

`update_os()` выполняет:

1. `apt update -y`
2. `apt upgrade -y`

Важно:

- обновление системы вызывается только один раз при старте приложения из `main.py`
- сервисы не должны сами вызывать `update_os()` внутри `install()`

## permission_utils.py

`check_root()` выбрасывает `PermissionError`, если приложение запущено не от имени `root`.

Это верхнеуровневая защита, используемая из `main.py`.

## args_utils.py

Поддерживаемые аргументы:

- `--mode {dev,prod}`
- `--install <codes...>`
- `--uninstall <codes...>`

Коды сервисов:

- `1=UFW`
- `2=BBR`
- `3=Docker`
- `4=Fail2Ban`
- `5=TrafficGuard`
- `6=UV`

В тестовом контексте (`pytest`) модуль не парсит CLI автоматически и создаёт упрощённый объект `app_args` с:

- `mode="prod"`
- `install=None`
- `uninstall=None`

Это позволяет импортировать модули без побочного разбора аргументов командной строки.
