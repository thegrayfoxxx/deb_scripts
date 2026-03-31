"""Тесты для интерактивного модуля UFW."""

from unittest.mock import Mock, patch

from app.interfaces.menu import ufw


class TestUfwInteractive:
    """Тесты для интерактивного интерфейса UFW."""

    def test_interactive_run_calls_menu_loop(self):
        """Тест что интерактивный запуск вызывает цикл меню."""
        with patch("app.interfaces.menu.ufw.run_menu_loop") as mock_run_menu_loop:
            ufw.interactive_run()
            mock_run_menu_loop.assert_called_once()

    def test_display_ufw_info_prints_content(self):
        """Тест отображения информации о UFW."""
        with patch("builtins.input"), patch("builtins.print") as mock_print:
            ufw.display_ufw_info()
            assert mock_print.call_count >= 1

    def test_open_specific_ports_cancel(self):
        """Тест отмены открытия специфичных портов."""
        mock_service = Mock()

        with patch("builtins.input", return_value="0"), patch("builtins.print"):
            ufw._open_specific_ports(mock_service)

        mock_service.open_port.assert_not_called()

    def test_close_specific_ports_cancel(self):
        """Тест отмены закрытия специфичных портов."""
        mock_service = Mock()

        with patch("builtins.input", return_value="0"), patch("builtins.print"):
            ufw._close_specific_ports(mock_service)

        mock_service.close_port.assert_not_called()

    def test_open_specific_ports_web_group(self):
        """Тест открытия веб-группы портов."""
        mock_service = Mock()
        mock_service.open_port.return_value = True

        with patch("builtins.input", return_value="2"), patch("builtins.print"):
            ufw._open_specific_ports(mock_service)

        for port in ("80", "443"):
            mock_service.open_port.assert_any_call(port)

    def test_open_specific_ports_multiple_groups(self):
        """Тест открытия нескольких групп портов."""
        mock_service = Mock()
        mock_service.open_port.return_value = True

        with patch("builtins.input", return_value="2 5"), patch("builtins.print"):
            ufw._open_specific_ports(mock_service)

        expected_ports = {"80", "443", "25", "587", "465", "143", "993", "110", "995"}
        for port in expected_ports:
            mock_service.open_port.assert_any_call(port)

    def test_open_specific_ports_all_groups_except_ssh(self):
        """Тест открытия всех групп портов кроме SSH."""
        mock_service = Mock()
        mock_service.open_port.return_value = True

        with patch("builtins.input", return_value="10"), patch("builtins.print"):
            ufw._open_specific_ports(mock_service)

        expected_ports = {
            "80",
            "443",
            "53",
            "67",
            "68",
            "25",
            "587",
            "465",
            "143",
            "993",
            "110",
            "995",
            "20",
            "21",
            "2222",
            "3306",
            "5432",
        }
        actual_ports = {call.args[0] for call in mock_service.open_port.call_args_list}
        assert actual_ports == expected_ports

    def test_close_specific_ports_all_groups_except_ssh(self):
        """Тест закрытия всех групп портов кроме SSH."""
        mock_service = Mock()
        mock_service.close_port.return_value = True

        with patch("builtins.input", return_value="10"), patch("builtins.print"):
            ufw._close_specific_ports(mock_service)

        expected_ports = {
            "80",
            "443",
            "53",
            "67",
            "68",
            "25",
            "587",
            "465",
            "143",
            "993",
            "110",
            "995",
            "20",
            "21",
            "2222",
            "3306",
            "5432",
        }
        actual_ports = {call.args[0] for call in mock_service.close_port.call_args_list}
        assert actual_ports == expected_ports

    def test_manage_custom_port_open_success(self):
        mock_service = Mock()
        mock_service.open_port.return_value = True

        with patch("builtins.input", return_value="8080"), patch("builtins.print"):
            ufw._manage_custom_port(mock_service, action="open")

        mock_service.open_port.assert_called_once_with("8080")

    def test_manage_custom_port_close_success(self):
        mock_service = Mock()
        mock_service.close_port.return_value = True

        with patch("builtins.input", return_value="8443/tcp"), patch("builtins.print"):
            ufw._manage_custom_port(mock_service, action="close")

        mock_service.close_port.assert_called_once_with("8443/tcp")

    def test_manage_custom_port_close_rejects_ssh(self):
        mock_service = Mock()

        with patch("builtins.input", return_value="22"), patch("builtins.print"):
            ufw._manage_custom_port(mock_service, action="close")

        mock_service.close_port.assert_not_called()

    @patch("builtins.input", side_effect=["invalid", "0"])
    @patch("builtins.print")
    def test_open_specific_ports_invalid_input(self, mock_print, mock_input):
        """Тест некорректного ввода при открытии специфичных портов."""
        mock_service = Mock()

        with patch("builtins.input", return_value="999"):
            ufw._open_specific_ports(mock_service)

        mock_service.open_port.assert_not_called()
