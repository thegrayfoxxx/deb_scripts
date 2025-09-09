# 🐍 DevOps Automation Scripts

![GitHub](https://img.shields.io/github/license/thegrayfoxxx/deb_scripts?color=blue)
![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)
![UV](https://img.shields.io/badge/UV-0.6.0%2B-orange?logo=python)

**Набор Python-скриптов для автоматизации DevOps-задач в Linux-окружении**
Упрощение настройки серверов, оптимизации сетевых параметров и безопасности.

---

## 🚀 Основные возможности

- **Автоматизация настройки сервера**: BBR, Fail2Ban и другие оптимизации
- **DEB**: поддержка Debian, Ubuntu и производных дистрибутивов
- **Экосистема инструментов**:
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
# Создание виртуального окружения, его активация и установка зависимостей из lock-файла
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

## 🖥️ Запуск

### UV
```bash
uv run main.py
```

### Запуск с помощью Python
```bash
python3 main.py
```

---

## 📂 Структура проекта
```
deb_scripts/
├── scripts/                  # Основные модули
│   ├── bbr.py                # Управление сетевыми параметрами
│   ├── docker.py             # Установка и настройка Docker
│   ├── fail2ban.py           # Конфигурация системы безопасности
│   └── uv.py                 # Установка и настройка uv
├── utils/                    # Утилиты и вспомогательные функции
│   └── subprocess_utils.py   # Вспомогательные функции
├── .gitignore                # Игнорируемые файлы и директории
├── .python-version           # Рекомендуемая версия Python
├── LICENSE                   # Лицензия проекта
├── main.py                   # Главный CLI-интерфейс
├── pyproject.toml            # Конфигурация проекта и зависимостей
└── README.md                 # Эта документация
```

---

## ⚠️ Безопасность

**Важно!** Скрипты выполняют системные изменения.

---

## 📜 Лицензия

MIT License © 2025 thegrayfoxxx
