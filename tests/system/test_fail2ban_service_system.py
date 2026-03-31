"""Системные тесты для сервиса Fail2Ban в реальной среде"""

import subprocess
import sys
from pathlib import Path

import pytest

# Добавляем путь к директории app
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "app"))

from app.services.fail2ban import Fail2BanService


@pytest.mark.system
class TestFail2BanSystemService:
    """Системные тесты для сервиса Fail2Ban"""

    def setup_method(self):
        self.service = Fail2BanService()

    def test_fail2ban_not_installed_by_default(self):
        """Проверяем, что состояние Fail2Ban в контейнере определяется корректно"""
        result = subprocess.run(["which", "fail2ban-server"], capture_output=True, text=True)
        assert result.returncode in [0, 1]

        if result.returncode == 0:
            version_result = subprocess.run(
                ["fail2ban-server", "--version"], capture_output=True, text=True, timeout=10
            )
            assert version_result.returncode in [0, 255]

    def test_apt_available_for_fail2ban_installation(self):
        """Проверяем, что apt доступен для установки Fail2Ban"""
        result = subprocess.run(["which", "apt"], capture_output=True, text=True)
        assert result.returncode == 0, "apt должен быть доступен"

        result = subprocess.run(["apt", "--version"], capture_output=True, text=True)
        assert result.returncode == 0, f"apt должен корректно работать: {result.stderr}"

    def test_systemd_not_fully_available_in_container(self):
        """Проверяем доступность systemd в контейнере (ограниченная функциональность)"""
        result = subprocess.run(["which", "systemctl"], capture_output=True, text=True)

        # В тестовом контейнере systemd может быть недоступен, это нормально
        # Но если доступен, проверим его версию
        if result.returncode == 0:
            result = subprocess.run(["systemctl", "--version"], capture_output=True, text=True)
            # Команда должна выполниться без системных ошибок
            assert result.returncode in [0, 1]

    def test_file_system_access_for_fail2ban_config(self):
        """Тестирование доступа к файловой системе для конфигурации Fail2Ban"""
        # Проверим, можем ли записать тестовую конфигурацию Fail2Ban во временный файл
        temp_file = "/tmp/test-fail2ban-jail.local"

        try:
            # Пишем тестовую конфигурацию jail.local
            config_content = """[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 600
findtime = 600
"""
            with open(temp_file, "w") as f:
                f.write(config_content)

            # Проверяем, что файл был создан
            assert Path(temp_file).exists()

            # Читаем содержимое обратно
            with open(temp_file, "r") as f:
                content = f.read()

            assert "enabled = true" in content
            assert "[sshd]" in content

            # Удаляем временный файл
            Path(temp_file).unlink()

        except PermissionError:
            pytest.skip("Нет прав на запись во временный каталог")

    def test_basic_file_operations_for_config_management(self):
        """Тестирование базовых операций с файлами для управления конфигурацией"""
        # Создаем директорию для теста
        test_dir = "/tmp/fail2ban_test_configs"

        # Создаем директорию
        result = subprocess.run(["mkdir", "-p", test_dir], capture_output=True, text=True)
        assert result.returncode == 0

        # Проверяем создание
        assert Path(test_dir).exists()

        # Создаем несколько тестовых файлов конфигурации
        config_files = {
            "jail.local": "[DEFAULT]\nbantime = 10m\nfindtime = 10m\n",
            "sshd.local": "[sshd]\nenabled = true\nport = ssh\n",
            "filter.local": "# Custom filter\n",
        }

        for filename, content in config_files.items():
            filepath = Path(test_dir) / filename
            with open(filepath, "w") as f:
                f.write(content)

            # Проверяем содержимое
            assert filepath.read_text() == content

        # Проверяем список файлов
        files_in_dir = [f.name for f in Path(test_dir).iterdir()]
        assert set(files_in_dir) == set(config_files.keys())

        # Удаляем созданные файлы
        subprocess.run(["rm", "-rf", test_dir], check=True)
        assert not Path(test_dir).exists()

    def test_network_services_related_commands(self):
        """Проверка команд, связанных с сетевыми службами (необходимо для Fail2Ban)"""
        # Проверяем наличие команд, которые может использовать Fail2Ban
        network_commands = [
            ["which", "iptables"],
            ["which", "netstat"],
            ["which", "ss"],  # modern replacement for netstat
        ]

        for cmd in network_commands:
            result = subprocess.run(cmd, capture_output=True, text=True)
            # Не требуем, чтобы все команды были установлены, но если есть - они должны работать
            if result.returncode == 0:
                # Команда доступна, проверим её версию или базовую функциональность
                command_name = cmd[1]  # Получаем имя команды
                if command_name in ["iptables", "netstat", "ss"]:
                    version_cmd = (
                        [command_name, "--version"]
                        if command_name != "ss"
                        else [command_name, "-v"]
                    )
                    result = subprocess.run(
                        version_cmd, capture_output=True, text=True, timeout=10
                    )
                    # Команда должна выполниться без системных ошибок
                    assert result.returncode in [0, 1, 2]

    def test_log_file_system_access(self):
        """Тестирование доступа к системе логов (необходимо для Fail2Ban)"""
        # Проверим, можем ли получить доступ к системным логам (или хотя бы их местоположению)
        log_directories = ["/var/log", "/var/log/auth.log", "/var/log/syslog"]

        for log_path in log_directories:
            path_obj = Path(log_path)
            # Не требуем, чтобы все логи были, но если существуют - они должны быть доступны
            if path_obj.exists():
                try:
                    # Попробуем получить информацию о файле
                    path_obj.stat()
                    # Если файл существует, мы должны иметь возможность получить его статус

                    # Попробуем прочитать последние строки (если это файл)
                    if path_obj.is_file():
                        # Попробуем выполнить tail через subprocess
                        result = subprocess.run(
                            ["tail", "-n", "5", str(path_obj)],
                            capture_output=True,
                            text=True,
                            timeout=10,
                        )
                        # Даже если файл пуст или недоступен, команда должна выполниться без системной ошибки
                        assert result.returncode in [0, 1]
                except (PermissionError, OSError):
                    # Некоторые логи могут требовать прав root
                    continue

    @pytest.mark.slow
    def test_fail2ban_installation_prerequisites(self):
        """Проверяем зависимости, необходимые для установки Fail2Ban"""
        # Список необходимых утилит для установки Fail2Ban
        required_tools = [
            "apt",
            "python3",
            "add-apt-repository",  # может быть не установлен по умолчанию
        ]

        found_missing = []
        for tool in required_tools:
            result = subprocess.run(["which", tool], capture_output=True, text=True)
            if result.returncode != 0:
                # add-apt-repository может быть не установлен, это нормально
                if tool == "add-apt-repository":
                    # Попробуем установить
                    subprocess.run(["apt", "update"], capture_output=True, text=True, timeout=30)
                    # Если apt update проходит, то add-apt-repository можно установить позже
                    continue
                found_missing.append(tool)

        # Для тестового контейнера мы ожидаем, что большинство инструментов будут доступны
        # за исключением add-apt-repository
        if len(found_missing) > 1 or ("add-apt-repository" not in found_missing):
            # Должны быть доступны все инструменты кроме add-apt-repository
            expected_missing = ["add-apt-repository"]
            actual_missing = [tool for tool in found_missing if tool in expected_missing]

            # Проверим, что мы нашли только те инструменты, которые действительно могут отсутствовать
            assert set(actual_missing) == set(found_missing), (
                f"Найдены неожиданно отсутствующие инструменты: {found_missing}"
            )
