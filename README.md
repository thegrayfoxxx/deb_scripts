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

## 🖥️ Примеры использования

### Настройка BBR (оптимизация TCP)
```bash
python ./scripts/bbr.py
```

### Конфигурация Fail2Ban
```bash
python ./scripts/fail2ban.py
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
├── main.py                # Главный CLI-интерфейс
├── .python-version        # Рекомендуемая версия Python
└── README.md              # Эта документация
```

---

## ⚠️ Безопасность

**Важно!** Скрипты выполняют системные изменения.

---

## 📜 Лицензия

MIT License © 2025 thegrayfoxxx
