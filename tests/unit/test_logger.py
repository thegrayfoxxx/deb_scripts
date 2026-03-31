"""Тесты для логгера."""

import logging
from unittest.mock import Mock, patch

from app.bootstrap.logger import get_logger, set_default_console_level


class TestLogger:
    """Тесты для логгера."""

    def test_get_logger_production_mode(self):
        """Тест получения логгера в продакшен режиме"""
        set_default_console_level("info")
        logger = get_logger("test_logger_prod_clean")
        assert logger.name == "test_logger_prod_clean"
        assert logger.level == logging.DEBUG

    def test_get_logger_development_mode(self):
        """Тест получения логгера в режиме разработки"""
        set_default_console_level("debug")
        logger = get_logger("test_logger_dev")
        assert logger.name == "test_logger_dev"
        assert logger.level == logging.DEBUG

    @patch("pathlib.Path.mkdir")
    @patch("logging.FileHandler")
    @patch("logging.StreamHandler")
    def test_get_logger_creates_handlers_once(
        self, mock_stream_handler, mock_file_handler, mock_mkdir
    ):
        """Тест что логгер создает обработчики только один раз"""
        set_default_console_level("info")
        mock_stream_handler_instance = Mock()
        mock_file_handler_instance = Mock()
        mock_stream_handler.return_value = mock_stream_handler_instance
        mock_file_handler.return_value = mock_file_handler_instance

        logger1 = get_logger("test_single_creation")
        logger2 = get_logger("test_single_creation")

        assert logger1.handlers == logger2.handlers
        assert len(logger1.handlers) == 2

    @patch("pathlib.Path.mkdir")
    @patch("logging.FileHandler")
    @patch("logging.StreamHandler")
    def test_get_logger_with_custom_file(self, mock_stream_handler, mock_file_handler, mock_mkdir):
        """Тест получения логгера с пользовательским файлом"""
        set_default_console_level("info")
        logger = get_logger("test_custom_file", log_file="custom.log")
        assert logger.name == "test_custom_file"

    @patch("pathlib.Path.mkdir")
    @patch("logging.FileHandler")
    @patch("logging.StreamHandler")
    def test_get_logger_with_custom_level(
        self, mock_stream_handler, mock_file_handler, mock_mkdir
    ):
        """Тест получения логгера с пользовательским уровнем"""
        set_default_console_level("info")
        logger = get_logger("test_custom_level", level=logging.WARNING)
        assert logger.name == "test_custom_level"
        assert logger.level == logging.DEBUG

    @patch("pathlib.Path.mkdir")
    @patch("logging.FileHandler", side_effect=PermissionError("denied"))
    @patch("logging.StreamHandler")
    def test_get_logger_skips_file_handler_on_permission_error(
        self, mock_stream_handler, mock_file_handler, mock_mkdir
    ):
        """Тест что логгер не падает, если файл логов недоступен."""
        set_default_console_level("info")
        mock_stream_handler_instance = Mock()
        mock_stream_handler.return_value = mock_stream_handler_instance

        logger = get_logger("test_file_handler_permission_error")

        assert logger.name == "test_file_handler_permission_error"
        assert len(logger.handlers) == 1
