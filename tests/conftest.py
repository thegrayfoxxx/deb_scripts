import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Добавляем путь к директории app, чтобы тесты могли импортировать модули
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def mock_subprocess_result():
    """Фикстура для создания mock результатов subprocess"""

    def _create_mock(returncode=0, stdout="", stderr=""):
        mock_result = Mock()
        mock_result.returncode = returncode
        mock_result.stdout = stdout
        mock_result.stderr = stderr
        return mock_result

    return _create_mock


@pytest.fixture
def mock_logger():
    """Фикстура для mock логгера"""
    with patch("app.utils.logger.get_logger") as mock_get_logger:
        mock_logger_instance = Mock()
        mock_get_logger.return_value = mock_logger_instance
        yield mock_logger_instance


@pytest.fixture
def fake_path_exists():
    """Фикстура для mock проверки существования файлов"""
    with patch("pathlib.Path.exists") as mock_exists:
        yield mock_exists


@pytest.fixture
def fake_file_operations():
    """Фикстура для mock операций с файлами"""
    with patch("builtins.open") as mock_open, patch("pathlib.Path.mkdir") as mock_mkdir:
        yield mock_open, mock_mkdir


@pytest.fixture
def mock_write_config_file():
    """Фикстура для mock метода _write_config_file"""
    with patch("app.services.bbr.BBRService._write_config_file") as mock_write:
        yield mock_write


@pytest.fixture
def mock_bbr_write_config_file():
    """Фикстура для mock метода _write_config_file в BBRService"""
    with patch("app.services.bbr.BBRService._write_config_file") as mock_write:
        yield mock_write


@pytest.fixture
def mock_docker_write_config_file():
    """Фикстура для mock метода _write_config_file в DockerService"""
    with patch("app.services.docker.DockerService._write_config_file") as mock_write:
        yield mock_write


# Integration test fixtures
@pytest.fixture
def mock_all_subprocess_calls():
    """Фикстура для мокирования всех вызовов subprocess в интеграционных тестах"""
    with patch("app.utils.subprocess_utils.run") as mock_run:
        yield mock_run


@pytest.fixture
def mock_system_commands():
    """Фикстура для мокирования системных команд в интеграционных тестах"""
    with (
        patch("os.geteuid") as mock_geteuid,
        patch("app.utils.subprocess_utils.run") as mock_run,
    ):
        yield mock_geteuid, mock_run


def pytest_collection_modifyitems(config, items):
    """Добавляем метки для тестов автоматически на основе их типа"""
    for item in items:
        # Проверяем, есть ли уже маркер integration
        has_integration_marker = any(
            marker.name == "integration" for marker in item.iter_markers()
        )

        if has_integration_marker:
            # Уже отмечен как интеграционный тест
            continue
        elif any(marker.name == "system" for marker in item.iter_markers()):
            # Отмечен как системный тест
            continue
        else:
            # Добавляем маркер unit для всех остальных тестов
            item.add_marker(pytest.mark.unit)
