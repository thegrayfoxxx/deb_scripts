"""Тесты для модуля app.bootstrap.permissions"""

from unittest.mock import patch

import pytest

from app.bootstrap.permissions import check_root


class TestPermissionUtils:
    """Тесты для утилит проверки разрешений"""

    @patch("app.bootstrap.permissions.os.geteuid")
    def test_check_root_with_root_permissions(self, mock_geteuid):
        """Тест проверки прав суперпользователя когда пользователь root"""
        # Мокаем os.geteuid чтобы возвращал 0 (root)
        mock_geteuid.return_value = 0

        # Проверяем, что функция не выбрасывает исключение
        check_root()

        # Проверяем, что geteuid был вызван
        mock_geteuid.assert_called_once()

    @patch("app.bootstrap.permissions.os.geteuid")
    def test_check_root_without_root_permissions(self, mock_geteuid):
        """Тест проверки прав суперпользователя когда пользователь не root"""
        # Мокаем os.geteuid чтобы возвращал 1000 (обычный пользователь)
        mock_geteuid.return_value = 1000

        # Проверяем, что функция выбрасывает PermissionError
        with pytest.raises(PermissionError, match="Скрипт требует прав root \\(sudo\\)"):
            check_root()

        # Проверяем, что geteuid был вызван
        mock_geteuid.assert_called_once()
