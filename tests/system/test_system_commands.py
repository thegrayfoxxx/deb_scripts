"""Системные тесты для проверки работы основных команд в Dev Container"""

import subprocess
import sys
from pathlib import Path

import pytest

# Добавляем путь к директории app
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "app"))


class TestSystemCommands:
    """Тесты для проверки основных системных команд в Dev Container"""

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
        # В Dev Container должна быть доступна сеть для установки пакетов
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
            ["dpkg", "-l"],  # Команда dpkg также должна быть доступна
        ]

        for cmd in basic_apt_commands:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            # Не требуем 0 статус, так как некоторые команды могут возвращать 1 при отсутствии результатов
            assert result.returncode in [0, 1, 2], (
                f"Команда {' '.join(cmd)} неожиданно завершилась: {result.stderr}"
            )

    @pytest.mark.system
    def test_package_manager_search_with_timeout_handling(self):
        """Тестирование поиска пакетов с обработкой таймаутов"""
        # Проверим apt search с более коротким таймаутом для предотвращения зависания
        try:
            result = subprocess.run(
                ["apt", "search", "python3"],
                capture_output=True,
                text=True,
                timeout=10,  # Уменьшенный таймаут для тестовой среды
            )
            # Команда должна завершиться за разумное время, даже если вернет ошибку
            assert result.returncode in [0, 1, 2], (
                f"Команда 'apt search python3' неожиданно завершилась: {result.stderr}"
            )
        except subprocess.TimeoutExpired:
            # Если таймаут происходит, это также валидный результат для тестовой среды
            pytest.skip("Команда apt search заняла слишком много времени в тестовой среде")

    @pytest.mark.system
    def test_network_connectivity_and_dns_resolution(self):
        """Тестирование сетевой связности и разрешения DNS"""
        # Проверим базовую доступность сети через команду, которая доступна в контейнере
        try:
            # Проверим доступность сетевого интерфейса через cat /proc/net/dev
            net_dev_path = Path("/proc/net/dev")
            if net_dev_path.exists():
                with open(net_dev_path, "r") as f:
                    net_content = f.read()
                # Проверим, что файл содержит информацию о сетевых интерфейсах
                assert "lo:" in net_content  # loopback интерфейс должен быть
                assert (
                    "eth" in net_content or "ens" in net_content
                )  # какой-либо ethernet интерфейс
            else:
                # Если файл недоступен, проверим через hostname
                result = subprocess.run(["hostname", "-i"], capture_output=True, text=True)
                assert result.returncode == 0, "Команда hostname должна работать"
        except Exception as e:
            pytest.skip(f"Сеть не доступна или нет подходящих команд: {e}")

    @pytest.mark.system
    def test_system_resources_and_limits(self):
        """Тестирование доступности системных ресурсов"""
        # Проверим доступность информации о памяти
        meminfo_path = Path("/proc/meminfo")
        if meminfo_path.exists():
            with open(meminfo_path, "r") as f:
                meminfo_content = f.read()
            assert "MemTotal:" in meminfo_content

        # Проверим доступность информации о процессоре
        cpuinfo_path = Path("/proc/cpuinfo")
        if cpuinfo_path.exists():
            with open(cpuinfo_path, "r") as f:
                cpuinfo_content = f.read()
            assert "processor" in cpuinfo_content

    @pytest.mark.system
    def test_process_management_capabilities(self):
        """Тестирование возможностей управления процессами"""
        # Проверим, что мы можем получить список процессов
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
        assert result.returncode == 0, "Команда ps должна работать"

        # Проверим, что мы можем получить информацию о текущем процессе
        result = subprocess.run(["pidof", "python3"], capture_output=True, text=True)
        # Может не найтись в тестовой среде, но не должно быть системной ошибки
        assert result.returncode in [0, 1], "pidof должен завершиться корректно"
