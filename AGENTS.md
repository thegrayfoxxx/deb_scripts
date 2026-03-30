# DevOps Automation Scripts

Этот файл задаёт верхнеуровневые правила для работы в `deb_scripts`.

## Проектные skills

Project-specific skills лежат в `.agents/skills/`.

- `.agents/skills/deb-scripts-maintainer/SKILL.md`
  - использовать для правок существующего кода, CLI, меню, логирования и документации
- `.agents/skills/deb-scripts-new-service/SKILL.md`
  - использовать при добавлении нового сервиса или расширении сервисного контракта
- `.agents/skills/deb-scripts-formatting/SKILL.md`
  - использовать для сортировки импортов и форматирования Python-кода через `uvx ruff`
- `.agents/skills/deb-scripts-logging/SKILL.md`
  - использовать при изменении логов, CLI-сообщений и интерактивного вывода
- `.agents/skills/deb-scripts-testing/SKILL.md`
  - использовать при выборе тестовой стратегии, смоук-проверок и обновлении тестов
- `.agents/skills/deb-scripts-cli-ux/SKILL.md`
  - использовать при изменении меню, prompt-ов, status-текста и другого пользовательского CLI-вывода
- `.agents/skills/deb-scripts-service-pattern/SKILL.md`
  - использовать при добавлении или рефакторинге сервисных классов в `app/services/`
- `.agents/skills/deb-scripts-system-commands/SKILL.md`
  - использовать при изменении `apt`, `systemctl`, `ufw`, `sysctl`, `curl`, `rm` и других системных команд
- `.agents/skills/deb-scripts-commits/SKILL.md`
  - использовать при написании commit message или PR title

Сначала выбирай подходящий skill, затем уже вноси изменения.

## Базовые правила

- Все системные изменения должны быть идемпотентными.
- Проект использует `Python 3.12+` как минимальную версию.
- Приложение предполагает запуск от `root`; не размывай это требование.
- Не ломай безопасный baseline для `UFW`: `deny incoming`, `allow outgoing`, SSH должен оставаться разрешённым.
- Не добавляй `apt update/upgrade` внутрь отдельных сервисов; обновление ОС должно оставаться централизованным в `main.py`.
- Сервисы содержат бизнес-логику, интерфейсы только маршрутизацию и UI.
- Используй общий логгер и существующие helper'ы вместо дублирования логики.
- Интерактивные меню должны оставаться loop-based и использовать общие утилиты меню/статусов.
- Для Python-форматирования используй `uvx ruff`; сортируй импорты и соблюдай длину строки `99`.
- Для логов и CLI-вывода используй явные уровни логирования; избегай перегруза пользователя внутренней телеметрией.
- Если изменение логически тянет на релизный bump, обновляй версию через `uv version` по semver и добавляй соответствующий Git tag.
- Любое изменение поведения должно сопровождаться обновлением тестов и, если нужно, `README.md`.

## Быстрая навигация

- `main.py` — точка входа и единичный вызов `update_os()`
- `app/services/` — операционная логика
- `app/interfaces/cli/` — неинтерактивный CLI
- `app/interfaces/interactive/` — интерактивные меню
- `app/utils/` — общие helper'ы
- `tests/` — unit, integration и system coverage
