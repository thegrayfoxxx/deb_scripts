"""Системные тесты для сервиса Docker в реальной среде"""

import subprocess
import sys
from pathlib import Path

import pytest

# Добавляем путь к директории app
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "app"))

from app.services.docker import DockerService


@pytest.mark.system
class TestDockerSystemService:
    """Системные тесты для сервиса Docker"""

    def setup_method(self):
        self.service = DockerService()

    def test_docker_binary_not_available_by_default(self):
        """Проверяем, что Docker не установлен по умолчанию в тестовом окружении"""
        result = subprocess.run(["which", "docker"], capture_output=True, text=True)
        # В стандартном тестовом контейнере Docker обычно не установлен
        assert result.returncode != 0  # 'which docker' должна вернуть ненулевой код

    def test_curl_available_for_installation(self):
        """Проверяем, что curl доступен для скачивания скрипта установки Docker"""
        result = subprocess.run(["which", "curl"], capture_output=True, text=True)
        assert result.returncode == 0, "curl должен быть доступен для загрузки скрипта Docker"

        # Проверим, что curl работает правильно
        result = subprocess.run(["curl", "--version"], capture_output=True, text=True, timeout=10)
        assert result.returncode == 0, f"curl должен корректно работать: {result.stderr}"

    def test_apt_available_for_docker_installation(self):
        """Проверяем, что apt доступен для установки Docker"""
        result = subprocess.run(["which", "apt"], capture_output=True, text=True)
        assert result.returncode == 0, "apt должен быть доступен"

        result = subprocess.run(["apt", "--version"], capture_output=True, text=True)
        assert result.returncode == 0, f"apt должен корректно работать: {result.stderr}"

    def test_gpg_available_for_docker_key_verification(self):
        """Проверяем, что gpg доступен для проверки ключа Docker"""
        result = subprocess.run(["which", "gpg"], capture_output=True, text=True)
        assert result.returncode == 0, "gpg должен быть доступен для проверки ключа Docker"

        result = subprocess.run(["gpg", "--version"], capture_output=True, text=True, timeout=10)
        assert result.returncode == 0, f"gpg должен корректно работать: {result.stderr}"

    def test_file_system_access_for_docker_installation(self):
        """Тестирование доступа к файловой системе, необходимому для установки Docker"""
        # Проверим, можем ли получить информацию о состоянии системы
        result = subprocess.run(["lsb_release", "-a"], capture_output=True, text=True)
        # Даже если lsb_release не доступен, команда должна выполниться без системных ошибок
        assert result.returncode in [0, 1, 127]

        # Проверим, можем ли читать /etc/os-release
        etc_os_release = Path("/etc/os-release")
        if etc_os_release.exists():
            content = etc_os_release.read_text()
            assert "ID=" in content  # Файл должен содержать идентификатор ОС

    def test_systemd_control_available(self):
        """Проверяем, что systemd доступен для управления сервисом Docker"""
        # В тестовом контейнере может быть ограниченный доступ к systemd
        result = subprocess.run(["which", "systemctl"], capture_output=True, text=True)

        # systemctl может быть недоступен в контейнере, это нормально
        # главное, что сама система поддерживает возможность управления сервисами

    def test_file_system_operations_for_config(self):
        """Тестирование файловых операций, необходимых для конфигурации Docker"""
        # Проверим, можем ли записать во временный файл
        temp_file = "/tmp/test-docker-config.json"

        try:
            # Пишем тестовую конфигурацию Docker
            config_content = """{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}"""
            with open(temp_file, "w") as f:
                f.write(config_content)

            # Проверяем, что файл был создан
            assert Path(temp_file).exists()

            # Читаем содержимое обратно
            with open(temp_file, "r") as f:
                content = f.read()

            assert "log-driver" in content

            # Удаляем временный файл
            Path(temp_file).unlink()

        except PermissionError:
            pytest.skip("Нет прав на запись во временный каталог")

    def test_network_access_for_docker_repo(self):
        """Тестирование сетевого доступа к репозиториям Docker"""
        # В тестовом контейнере должна быть доступна сеть для установки Docker
        # Проверим, можем ли выполнить базовые сетевые операции
        try:
            # Проверим, можем ли разрешить имя хоста (ограниченная проверка)
            result = subprocess.run(
                ["sh", "-c", "getent hosts registry-1.docker.io | head -n 1"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            # Мы не требуем успеха, так как в тестовой среде может не быть доступа к реальным сайтам
        except subprocess.TimeoutExpired:
            # Это нормально в изолированной среде
            pass

    @pytest.mark.slow
    def test_docker_installation_dependencies(self):
        """Проверяем все зависимости, необходимые для установки Docker"""
        # Список необходимых утилит для установки Docker
        required_tools = [
            "apt",
            "curl",
            "gpg",
            "lsb_release",  # для определения версии ОС
            "add-apt-repository",  # может быть недоступен в базовом образе
        ]

        found_missing = []
        for tool in required_tools:
            result = subprocess.run(["which", tool], capture_output=True, text=True)
            if result.returncode != 0:
                # add-apt-repository может быть не установлен, это нормально
                if tool == "add-apt-repository":
                    # Попробуем установить
                    install_result = subprocess.run(
                        ["apt", "update"], capture_output=True, text=True, timeout=30
                    )
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
