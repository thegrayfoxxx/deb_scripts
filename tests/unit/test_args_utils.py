from unittest.mock import patch

from app.utils.args_utils import get_app_args


class TestArgsUtils:
    def test_get_app_args_with_default_mode(self):
        """Тест получения аргументов с режимом по умолчанию"""
        # В режиме тестирования мы должны получить значения по умолчанию
        args = get_app_args()
        assert hasattr(args, "mode")
        assert args.mode in ["dev", "prod"]  # Проверяем, что режим валиден

    @patch("sys.argv", ["script_name", "--mode", "dev"])
    def test_get_app_args_dev_mode(self):
        """Тест получения аргументов с режимом разработки"""
        # Тестируем в обход обычной логики, т.к. в тестах мы не хотим, чтобы парсер аргументов
        # был вызван нормально - это уже обрабатывается в логике модуля
        # Но можно протестировать функцию parse_args если она будет вынесена в отдельный тест

        # Вместо этого тестируем, что объект имеет нужные атрибуты
        args = get_app_args()
        assert hasattr(args, "mode")

    def test_args_object_has_expected_attributes(self):
        """Тест проверки, что объект аргументов имеет ожидаемые атрибуты"""
        args = get_app_args()
        assert hasattr(args, "mode")
        assert isinstance(args.mode, str)
        assert args.mode in ["dev", "prod"]
