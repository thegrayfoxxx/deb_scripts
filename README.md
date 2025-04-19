# 🐍 DevOps Automation Scripts

![GitHub](https://img.shields.io/github/license/thegrayfoxxx/deb_scripts?color=blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![UV](https://img.shields.io/badge/UV-0.1%2B-orange?logo=python)

**Набор Python-скриптов для автоматизации DevOps-задач в Linux-окружении**
Упрощение настройки серверов, оптимизации сетевых параметров и безопасности.

---

## 🚀 Основные возможности

- **Автоматизация настройки сервера**: BBR, Fail2Ban и другие оптимизации
- **DEB**: поддержка Debian, Ubuntu и производных дистрибутивов
- **Экосистема инструментов**:
  - ✅ Ruff для линтинга и форматирования
  - ✅ UV для управления зависимостями

---

## ⚙️ Быстрый старт

### Предварительные требования
- Python 3.12+
- Git
- POSIX-совместимая оболочка (bash/zsh)

### Установка
```bash
git clone https://github.com/thegrayfoxxx/deb_scripts.git
cd deb_scripts
```

---

## 📦 Управление зависимостями

### Рекомендуемый способ (с UV)
```bash
# Создать виртуальное окружение и активировать
uv venv
source .venv/bin/activate

# Установить зависимости из lock-файла (рекомендуется для production)
uv sync
```

### Альтернативный способ (с PIP)
```bash
# Создать виртуальное окружение
python -m venv .venv
source .venv/bin/activate

# Установить зависимости (требуется предварительная генерация requirements.txt)
uv pip compile -o requirements.txt  # генерируем из pyproject.toml
pip install -r requirements.txt
```

---

## 🖥️ Примеры использования

### Настройка BBR (оптимизация TCP)
```bash
python ./scripts/bbr.py
```

### Конфигурация Fail2Ban
```bash
python ./scripts/fail2ban.py
```

### Форматирование кода
```bash
./format.sh  # Запускает ruff format и ruff check
```

---

## 📂 Структура проекта
```
deb_scripts/
├── scripts/               # Основные модули
│   ├── bbr.py             # Управление сетевыми параметрами
│   └── fail2ban.py        # Конфигурация системы безопасности
├── pyproject.toml         # Конфигурация проекта и зависимостей
├── uv.lock               ️ # Фиксированные версии пакетов
├── format.sh              # Скрипт форматирования кода
├── main.py                # Главный CLI-интерфейс
├── .python-version        # Рекомендуемая версия Python
└── README.md              # Эта документация
```

---

## 🛠️ Разработка

### Настройка окружения
```bash
uv venv
source .venv/bin/activate
uv sync --all-extras  # Установка dev-зависимостей
pre-commit install    # Активация git-хуков
```

### Рабочий процесс
Проверьте код перед коммитом:
```bash
./format.sh  # Автоисправление стиля
```

### Обновление зависимостей
```bash
uv sync  # Обновить uv.lock
```

---

## 🤝 Участие в проекте

Приветствуются любые вклады!

1. Форкните репозиторий
2. Создайте feature-ветку:
```bash
git checkout -b feat/awesome-feature
```
3. Зафиксируйте изменения с Conventional Commits:
```bash
git commit -m "feat: add awesome feature"
```
4. Откройте Pull Request с описанием изменений

---

## ⚠️ Безопасность

**Важно!** Скрипты выполняют системные изменения.

---

## 📜 Лицензия

MIT License © 2024 thegrayfoxxx
