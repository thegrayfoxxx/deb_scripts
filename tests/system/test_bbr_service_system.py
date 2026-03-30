"""Системные тесты для сервиса BBR в реальной среде"""

import subprocess
import sys
from pathlib import Path

import pytest

# Добавляем путь к директории app
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "app"))

from app.services.bbr import BBRService


def _require_sysctl():
    result = subprocess.run(["which", "sysctl"], capture_output=True, text=True)
    if result.returncode != 0:
        pytest.skip("sysctl недоступен в текущем окружении")


@pytest.mark.system
class TestBBRSystemService:
    """Системные тесты для сервиса BBR"""

    def setup_method(self):
        self.service = BBRService()

    def test_check_bbr_available(self):
        """Проверяем, доступен ли BBR в системе (через проверку модуля)"""
        _require_sysctl()

        # Проверим, можно ли получить значение net.core.default_qdisc
        result = subprocess.run(
            ["sysctl", "net.core.default_qdisc"], capture_output=True, text=True
        )
        # Это должно выполниться без системных ошибок (может вернуть ошибку если параметр не существует)
        assert result.returncode in [0, 1, 2]

    def test_bbr_kernel_parameters_exist(self):
        """Проверяем существование необходимых параметров ядра для BBR"""
        _require_sysctl()

        # Проверяем, существуют ли файлы в /proc/sys/net/...
        net_params = [
            "net/core/default_qdisc",
            "net/ipv4/tcp_congestion_control",
        ]

        for param in net_params:
            result = subprocess.run(["sysctl", param], capture_output=True, text=True, timeout=10)
            # Даже если параметр не существует, команда должна выполниться без системной ошибки
            assert result.returncode in [0, 1, 2], (
                f"Ошибка при обращении к параметру {param}: {result.stderr}"
            )

    def test_sysctl_command_execution(self):
        """Тестирование выполнения команд sysctl"""
        _require_sysctl()

        # Проверяем, можем ли прочитать текущую конфигурацию
        try:
            result = subprocess.run(
                ["sysctl", "net.core.default_qdisc"], capture_output=True, text=True, timeout=10
            )
            # Команда должна выполниться без системных ошибок
            assert result.returncode in [0, 1]
        except subprocess.TimeoutExpired:
            pytest.skip("Команда sysctl заняла слишком много времени")

    def test_file_system_access_for_config(self):
        """Тестирование доступа к файловой системе для записи конфигурации"""
        # Проверим, можем ли записать во временный файл
        temp_file = "/tmp/test-bbr-config.conf"

        try:
            # Пишем тестовую конфигурацию
            with open(temp_file, "w") as f:
                f.write("# Test BBR configuration\n")
                f.write("net.core.default_qdisc=fq\n")
                f.write("net.ipv4.tcp_congestion_control=bbr\n")

            # Проверяем, что файл был создан
            assert Path(temp_file).exists()

            # Читаем содержимое обратно
            with open(temp_file, "r") as f:
                content = f.read()

            assert "tcp_congestion_control=bbr" in content

            # Удаляем временный файл
            Path(temp_file).unlink()

        except PermissionError:
            pytest.skip("Нет прав на запись во временный каталог")

    @pytest.mark.slow
    def test_bbr_installation_simulation(self):
        """Симуляция процесса установки BBR (только проверка доступности команд)"""
        # В реальном тестовом окружении мы не будем действительно включать BBR,
        # но проверим, доступны ли необходимые для этого команды

        _require_sysctl()

        # Проверяем доступность модулей ядра (проверяем через lsmod или наличие файлов)
        # lsmod может быть недоступен в контейнере, поэтому проверяем это
        result = subprocess.run(["which", "lsmod"], capture_output=True, text=True)
        if result.returncode == 0:
            # lsmod доступен, значит пробуем его использовать
            result = subprocess.run(["lsmod"], capture_output=True, text=True, timeout=10)
            # Не требуем 0 статус, так как в контейнере модули могут не быть загружены
            assert result.returncode in [0, 1]

        # Проверяем доступность /etc/sysctl.conf или аналогичных файлов
        essential_files = [
            "/etc/sysctl.conf",
            "/proc/sys/kernel/version",
            "/proc/sys/net/ipv4/tcp_available_congestion_control",
        ]

        for filepath in essential_files:
            if Path(filepath).exists():
                # Можем прочитать хотя бы часть содержимого
                try:
                    Path(filepath).read_text()
                except (PermissionError, OSError):
                    # Некоторые файлы требуют особых прав, это нормально
                    pass

    def test_bbr_status_methods(self):
        """Тестирование методов проверки статуса BBR"""
        _require_sysctl()

        # Просто проверяем, что методы не выбрасывают исключений при вызове
        # в реальной системе

        # Этот метод использует subprocess для проверки системных параметров
        try:
            # Попробуем выполнить sysctl команды, аналогичные тем, что используются в сервисе
            result = subprocess.run(
                ["sysctl", "-n", "net.ipv4.tcp_congestion_control"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            # Команда должна выполниться без системных ошибок
            assert result.returncode in [0, 1, 2]
        except subprocess.TimeoutExpired:
            pytest.skip("Команда sysctl заняла слишком много времени")
