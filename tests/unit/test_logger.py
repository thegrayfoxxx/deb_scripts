"""Тесты для логгера."""

from unittest.mock import Mock, patch

from app.utils.logger import get_logger


class TestLogger:
    """Тесты для логгера."""

    @patch("app.utils.logger.app_args")
    def test_get_logger_production_mode(self, mock_app_args):
        """Тест получения логгера в продакшен режиме"""
        mock_app_args.mode = "prod"

        logger = get_logger("test_logger_prod")
        assert logger.name == "test_logger_prod"

    @patch("app.utils.logger.app_args")
    def test_get_logger_development_mode(self, mock_app_args):
        """Тест получения логгера в режиме разработки"""
        mock_app_args.mode = "dev"

        logger = get_logger("test_logger_dev")
        assert logger.name == "test_logger_dev"

    @patch("app.utils.logger.app_args")
    @patch("pathlib.Path.mkdir")
    @patch("logging.FileHandler")
    @patch("logging.StreamHandler")
    def test_get_logger_creates_handlers_once(
        self, mock_stream_handler, mock_file_handler, mock_mkdir, mock_app_args
    ):
        """Тест что логгер создает обработчики только один раз"""
        mock_app_args.mode = "prod"
        mock_stream_handler_instance = Mock()
        mock_file_handler_instance = Mock()
        mock_stream_handler.return_value = mock_stream_handler_instance
        mock_file_handler.return_value = mock_file_handler_instance

        logger1 = get_logger("test_single_creation")
        logger2 = get_logger("test_single_creation")

        assert logger1.handlers == logger2.handlers
        assert len(logger1.handlers) == 2

    @patch("app.utils.logger.app_args")
    @patch("pathlib.Path.mkdir")
    @patch("logging.FileHandler")
    @patch("logging.StreamHandler")
    def test_get_logger_with_custom_file(
        self, mock_stream_handler, mock_file_handler, mock_mkdir, mock_app_args
    ):
        """Тест получения логгера с пользовательским файлом"""
        mock_app_args.mode = "prod"

        logger = get_logger("test_custom_file", log_file="custom.log")
        assert logger.name == "test_custom_file"

    @patch("app.utils.logger.app_args")
    @patch("pathlib.Path.mkdir")
    @patch("logging.FileHandler")
    @patch("logging.StreamHandler")
    def test_get_logger_with_custom_level(
        self, mock_stream_handler, mock_file_handler, mock_mkdir, mock_app_args
    ):
        """Тест получения логгера с пользовательским уровнем"""
        mock_app_args.mode = "prod"

        import logging

        logger = get_logger("test_custom_level", level=logging.WARNING)
        assert logger.name == "test_custom_level"
        assert logger.level == logging.WARNING

    @patch("app.utils.logger.app_args")
    @patch("pathlib.Path.mkdir")
    @patch("logging.FileHandler", side_effect=PermissionError("denied"))
    @patch("logging.StreamHandler")
    def test_get_logger_skips_file_handler_on_permission_error(
        self, mock_stream_handler, mock_file_handler, mock_mkdir, mock_app_args
    ):
        """Тест что логгер не падает, если файл логов недоступен."""
        mock_app_args.mode = "prod"
        mock_stream_handler_instance = Mock()
        mock_stream_handler.return_value = mock_stream_handler_instance

        logger = get_logger("test_file_handler_permission_error")

        assert logger.name == "test_file_handler_permission_error"
        assert len(logger.handlers) == 1
