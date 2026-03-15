# 🐍 DevOps Automation Scripts

![GitHub](https://img.shields.io/github/license/thegrayfoxxx/deb_scripts?color=blue)
![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)
![UV](https://img.shields.io/badge/UV-0.6.0%2B-orange?logo=python)

**Набор Python-скриптов для автоматизации DevOps-задач в Linux-окружении**
Упрощение настройки серверов, оптимизации сетевых параметров и безопасности.

---

## 🚀 Основные возможности

- **Автоматизация настройки сервера**: BBR, Fail2Ban, Docker, TrafficGuard
- **Поддержка дистрибутивов**: Debian, Ubuntu и производные (apt-based)
- **Интерактивный CLI**: удобное меню для выбора операций
- **Идемпотентность**: безопасный многократный запуск
- **Логирование**: подробные логи в файле `app.log`

### 📦 Доступные сервисы

| Сервис | Описание |
|--------|----------|
| **BBR** | Включение/выключение алгоритма перегрузки BBR для оптимизации сети |
| **Docker** | Установка и полное удаление Docker Engine |
| **Fail2Ban** | Защита SSH через настройку Fail2Ban с jail для sshd |
| **TrafficGuard** | Установка и удаление TrafficGuard (защита от сканеров портов) |
| **UV** | Установка и удаление менеджера пакетов UV (Astral) |


---

## ⚙️ Быстрый старт

### Предварительные требования
- Python 3.12+
- Git
- POSIX-совместимая оболочка (bash/zsh)
- **Права root** (требуется `sudo` для выполнения скриптов)

### Установка
```bash
git clone https://github.com/thegrayfoxxx/deb_scripts.git
cd deb_scripts
```

---

## 📦 Управление зависимостями

Проект не имеет внешних зависимостей — используются только стандартные модули Python (`subprocess`, `logging`, `pathlib`, `os`, `argparse`).

### Опционально: виртуальное окружение с UV
```bash
# Создание и активация виртуального окружения
uv venv
source .venv/bin/activate
```

### Альтернативный способ (с venv)
```bash
# Создать виртуальное окружение
python -m venv .venv
source .venv/bin/activate
```

---

## 🖥️ Запуск

### ⚠️ Требуется root
Все скрипты выполняют системные изменения — запуск только с правами суперпользователя:

```bash
# Через run.sh
sudo ./run.sh

# Или напрямую
sudo python3 main.py

# Или через uv (если установлен)
sudo uv run main.py
```

### 🎯 Интерактивное меню
После запуска вам будет предложено выбрать сервис:
```
Добро пожаловать в deb_scripts!
Выберите скрипт:
BBR - 1
Docker - 2
Fail2Ban - 3
TrafficGuard - 4
UV - 5
Выход - 0
```

---

## 📂 Структура проекта
```
deb_scripts/
├── app/
│   ├── interfaces/
│   │   ├── interactive/     # Интерактивные меню для каждого сервиса
│   │   │   ├── run.py       # Главное меню
│   │   │   ├── bbr.py
│   │   │   ├── docker.py
│   │   │   ├── fail2ban.py
│   │   │   ├── uv.py
│   │   │   └── traffic_guard.py
│   │   └── cli/             # (зарезервировано для CLI-режима)
│   ├── services/
│   │   ├── bbr.py           # Логика BBR
│   │   ├── docker.py        # Логика Docker
│   │   ├── fail2ban.py      # Логика Fail2Ban
│   │   ├── uv.py            # Логика UV
│   │   └── traffic_guard.py # Логика TrafficGuard
│   └── utils/
│       ├── logger.py        # Настройка логгера
│       ├── subprocess_utils.py # Утилиты для запуска команд
│       ├── update_utils.py  # Обновление ОС (apt update/upgrade)
│       ├── permission_utils.py # Проверка прав root
│       └── args_utils.py    # Парсинг аргументов (--mode dev/prod)
├── .gitignore
├── .python-version
├── LICENSE
├── main.py                  # Точка входа
├── pyproject.toml
├── README.md
└── run.sh                   # Обёртка для запуска
```

---

## 🔧 Режимы работы

```bash
# Продакшен (по умолчанию)
sudo python3 main.py

# Разработка (включает DEBUG-логирование)
sudo python3 main.py --mode dev
```

---

## 📝 Логирование

Все операции логируются в файл `app.log` с детализацией:
- Время события
- Имя модуля
- Уровень (INFO/DEBUG/ERROR)
- Сообщение

Пример:
```
2025-03-15 10:30:45 - BBRService - INFO - 🚀 Начало включения BBR...
2025-03-15 10:30:46 - BBRService - DEBUG - 📦 Модуль tcp_bbr успешно загружен
2025-03-15 10:30:47 - BBRService - INFO - ✅ BBR успешно включен (алгоритм: bbr) 🎉
```

---

## ⚠️ Безопасность

**Важно!** Скрипты выполняют системные изменения:
- Установка/удаление пакетов
- Изменение конфигурации ядра (sysctl)
- Управление службами systemd
- Модификация файлов в `/etc/`

**Всегда проверяйте изменения перед запуском в продакшене!**

---

## 🤝 Вклад

1. Fork репозитория
2. Создайте ветку (`git checkout -b feature/amazing-feature`)
3. Закоммитьте изменения (`git commit -m 'Add amazing feature'`)
4. Запушьте (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

---

## 📜 Лицензия

MIT License © 2025 thegrayfoxxx
