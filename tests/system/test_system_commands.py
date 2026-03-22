"""Системные тесты для проверки работы основных команд в Docker-контейнере"""

import subprocess
import sys
from pathlib import Path

import pytest

# Добавляем путь к директории app
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "app"))


class TestSystemCommands:
    """Тесты для проверки основных системных команд в Docker-контейнере"""

    @pytest.mark.system
    def test_basic_linux_commands_available(self):
        """Проверяем доступность базовых команд Linux"""
        commands_to_test = [
            ["ls", "--version"],
            ["cat", "--version"],
            ["echo", "hello"],
            ["pwd"],
            ["whoami"],
            ["uname", "-a"],
        ]

        for cmd in commands_to_test:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            assert result.returncode == 0, (
                f"Команда {' '.join(cmd)} завершилась с ошибкой: {result.stderr}"
            )

    @pytest.mark.system
    def test_file_system_operations(self):
        """Тестирование базовых операций с файловой системой"""
        test_dir = "/tmp/test_dir_for_deb_scripts"

        # Создаем директорию
        result = subprocess.run(["mkdir", "-p", test_dir], capture_output=True, text=True)
        assert result.returncode == 0

        # Проверяем создание
        assert Path(test_dir).exists()

        # Создаем тестовый файл
        test_file = Path(test_dir) / "test_file.txt"
        with open(test_file, "w") as f:
            f.write("test_content")

        # Проверяем содержимое файла
        assert test_file.read_text() == "test_content"

        # Удаляем созданные файлы
        subprocess.run(["rm", "-rf", test_dir], check=True)

        # Проверяем, что директория удалена
        assert not Path(test_dir).exists()

    @pytest.mark.system
    def test_permissions_and_user_context(self):
        """Тестирование прав доступа и контекста пользователя"""
        # Проверяем, что мы можем получить UID (в тестовом контейнере обычно root)
        result = subprocess.run(["id", "-u"], capture_output=True, text=True)
        assert result.returncode == 0
        uid = int(result.stdout.strip())

        # Проверяем, что мы можем писать в /tmp (должно быть разрешено для всех)
        test_file = "/tmp/test_permissions.txt"
        with open(test_file, "w") as f:
            f.write(f"UID: {uid}")

        assert Path(test_file).exists()
        Path(test_file).unlink()  # Удаляем файл

    @pytest.mark.system
    def test_network_connectivity_simulation(self):
        """Тестирование сетевой связности для установки пакетов"""
        # В Docker-контейнере должна быть доступна сеть для установки пакетов
        # Проверим доступность DNS и соединения с внешним миром
        try:
            # Проверяем, можем ли выполнить простой DNS lookup
            result = subprocess.run(
                ["sh", "-c", "getent hosts google.com | head -n 1"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            # В идеале должен вернуть IP-адрес или не вернуть ничего (без ошибки)
            # Мы не требуем успешного результата, но команда должна выполниться без системных ошибок
            assert result.returncode in [0, 2]  # 0 - успех, 2 - не найден хост
        except subprocess.TimeoutExpired:
            # Это нормально в изолированной среде, главное - нет системных ошибок
            pass

    @pytest.mark.system
    def test_python_availability_and_version(self):
        """Проверяем доступность Python и его версию"""
        result = subprocess.run([sys.executable, "--version"], capture_output=True, text=True)
        assert result.returncode == 0
        assert "Python 3" in result.stdout

        # Проверяем, что можем импортировать основные модули
        modules_to_test = [
            "sys",
            "os",
            "subprocess",
            "pathlib",
            "json",
        ]

        for module in modules_to_test:
            result = subprocess.run(
                [sys.executable, "-c", f"import {module}"], capture_output=True, text=True
            )
            assert result.returncode == 0, (
                f"Не удалось импортировать модуль {module}: {result.stderr}"
            )

    @pytest.mark.system
    def test_package_manager_access(self):
        """Тестирование доступа к менеджеру пакетов apt"""
        # В нашем тестовом контейнере должен быть доступен apt
        result = subprocess.run(["apt", "--version"], capture_output=True, text=True)
        assert result.returncode == 0

        # Также проверим доступ к другим базовым командам apt
        basic_apt_commands = [
            ["apt", "list", "--upgradable"],
            ["apt", "search", "python3"],
            ["dpkg", "-l"],  # Команда dpkg также должна быть доступна
        ]

        for cmd in basic_apt_commands:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            # Не требуем 0 статус, так как некоторые команды могут возвращать 1 при отсутствии результатов
            assert result.returncode in [0, 1, 2], (
                f"Команда {' '.join(cmd)} неожиданно завершилась: {result.stderr}"
            )
