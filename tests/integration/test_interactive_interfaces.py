"""Интеграционные тесты для интерактивных интерфейсов"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Добавляем путь к директории app
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "app"))

from app.interfaces.interactive import bbr, docker, fail2ban, run, traffic_guard, uv


@pytest.mark.integration
class TestInteractiveInterfacesIntegration:
    """Интеграционные тесты для интерактивных интерфейсов"""

    def test_docker_interactive_menu_flow_with_mocked_service(self):
        """Тест потока интерактивного меню Docker с замоканным сервисом"""
        # Мокаем сервис Docker
        mock_docker_service = Mock()

        with (
            patch(
                "app.interfaces.interactive.docker.DockerService",
                return_value=mock_docker_service,
            ),
            patch(
                "builtins.input", side_effect=["1", "0", "0"]
            ),  # Выбираем установку, затем выход, затем выход из главного меню
            patch("builtins.print"),
            patch("sys.exit"),  # Предотвращаем выход из системы
        ):
            # Вызываем интерактивный запуск Docker
            try:
                docker.interactive_run()
            except SystemExit:
                pass  # Нормально, так как sys.exit замокан

            # Проверяем, что был вызван метод установки
            mock_docker_service.install.assert_called_once()

    def test_docker_interactive_menu_uninstall_flow(self):
        """Тест потока интерактивного меню Docker - удаление"""
        # Мокаем сервис Docker
        mock_docker_service = Mock()

        with (
            patch(
                "app.interfaces.interactive.docker.DockerService",
                return_value=mock_docker_service,
            ),
            patch(
                "builtins.input", side_effect=["2", "0", "0"]
            ),  # Выбираем удаление, затем выход, затем выход из главного меню
            patch("builtins.print"),
            patch("sys.exit"),  # Предотвращаем выход из системы
        ):
            # Вызываем интерактивный запуск Docker
            try:
                docker.interactive_run()
            except SystemExit:
                pass  # Нормально, так как sys.exit замокан

            # Проверяем, что был вызван метод удаления
            mock_docker_service.uninstall.assert_called_once()

    def test_bbr_interactive_menu_enable_flow(self):
        """Тест потока интерактивного меню BBR - включение"""
        # Мокаем сервис BBR
        mock_bbr_service = Mock()

        with (
            patch(
                "app.interfaces.interactive.bbr.BBRService",
                return_value=mock_bbr_service,
            ),
            patch(
                "builtins.input", side_effect=["2", "0", "0"]
            ),  # Выбираем включение BBR, затем выход, затем выход из главного меню
            patch("builtins.print"),
            patch("sys.exit"),  # Предотвращаем выход из системы
        ):
            # Вызываем интерактивный запуск BBR
            try:
                bbr.interactive_run()
            except SystemExit:
                pass  # Нормально, так как sys.exit замокан

            # Проверяем, что был вызван метод включения BBR
            mock_bbr_service.activate.assert_called_once()

    def test_bbr_interactive_menu_disable_flow(self):
        """Тест потока интерактивного меню BBR - отключение"""
        # Мокаем сервис BBR
        mock_bbr_service = Mock()

        with (
            patch(
                "app.interfaces.interactive.bbr.BBRService",
                return_value=mock_bbr_service,
            ),
            patch(
                "builtins.input", side_effect=["3", "0", "0"]
            ),  # Выбираем отключение BBR, затем выход, затем выход из главного меню
            patch("builtins.print"),
            patch("sys.exit"),  # Предотвращаем выход из системы
        ):
            # Вызываем интерактивный запуск BBR
            try:
                bbr.interactive_run()
            except SystemExit:
                pass  # Нормально, так как sys.exit замокан

            # Проверяем, что был вызван метод отключения BBR
            mock_bbr_service.deactivate.assert_called_once()

    def test_fail2ban_interactive_menu_flow_with_mocked_service(self):
        """Тест потока интерактивного меню Fail2Ban с замоканным сервисом"""
        # Мокаем сервис Fail2Ban
        mock_fail2ban_service = Mock()

        with (
            patch(
                "app.interfaces.interactive.fail2ban.Fail2BanService",
                return_value=mock_fail2ban_service,
            ),
            patch(
                "builtins.input", side_effect=["1", "0", "0"]
            ),  # Выбираем установку, затем выход, затем выход из главного меню
            patch("builtins.print"),
            patch("sys.exit"),  # Предотвращаем выход из системы
        ):
            # Вызываем интерактивный запуск Fail2Ban
            try:
                fail2ban.interactive_run()
            except SystemExit:
                pass  # Нормально, так как sys.exit замокан

            # Проверяем, что был вызван метод установки
            mock_fail2ban_service.install.assert_called_once()

    def test_fail2ban_interactive_menu_uninstall_flow(self):
        """Тест потока интерактивного меню Fail2Ban - удаление"""
        # Мокаем сервис Fail2Ban
        mock_fail2ban_service = Mock()

        with (
            patch(
                "app.interfaces.interactive.fail2ban.Fail2BanService",
                return_value=mock_fail2ban_service,
            ),
            patch(
                "builtins.input", side_effect=["4", "0", "0"]
            ),  # Выбираем удаление, затем выход, затем выход из главного меню
            patch("builtins.print"),
            patch("sys.exit"),  # Предотвращаем выход из системы
        ):
            # Вызываем интерактивный запуск Fail2Ban
            try:
                fail2ban.interactive_run()
            except SystemExit:
                pass  # Нормально, так как sys.exit замокан

            # Проверяем, что был вызван метод удаления
            mock_fail2ban_service.uninstall.assert_called_once()

    def test_main_menu_selection_docker(self):
        """Тест выбора Docker в главном меню"""
        with (
            patch(
                "builtins.input", side_effect=["3", "0", "0"]
            ),  # Выбираем Docker, затем выход из Docker, затем выход из главного
            patch("builtins.print"),
            patch(
                "app.interfaces.interactive.docker.interactive_run"
            ) as mock_docker_run,
        ):
            try:
                run.run_interactive_script()
            except SystemExit:
                # Нормально, потому что в конце есть exit()
                pass

            # Проверяем, что был вызван Docker интерактивный интерфейс
            mock_docker_run.assert_called_once()

    def test_main_menu_selection_bbr(self):
        """Тест выбора BBR в главном меню"""
        with (
            patch(
                "builtins.input", side_effect=["2", "0", "0"]
            ),  # Выбираем BBR, затем выход из BBR, затем выход из главного
            patch("builtins.print"),
            patch("app.interfaces.interactive.bbr.interactive_run") as mock_bbr_run,
        ):
            try:
                run.run_interactive_script()
            except SystemExit:
                # Нормально, потому что в конце есть exit()
                pass

            # Проверяем, что был вызван BBR интерактивный интерфейс
            mock_bbr_run.assert_called_once()

    def test_main_menu_invalid_input(self):
        """Тест обработки неверного ввода в главном меню"""
        with (
            patch(
                "builtins.input", side_effect=["99", "0"]
            ),  # Неверный ввод, затем выход
            patch("builtins.print") as mock_print,
        ):
            try:
                run.run_interactive_script()
            except SystemExit:
                pass

            printed_texts = [
                call.args[0] for call in mock_print.call_args_list if call.args
            ]
            assert any(
                "❌ Неверный ввод, попробуйте снова" in text for text in printed_texts
            )

    def test_main_menu_exit_option(self):
        """Тест опции выхода из главного меню"""
        with (
            patch("builtins.input", side_effect=["0"]),  # Выбираем выход
            patch("builtins.print"),
        ):
            with pytest.raises(SystemExit):
                run.run_interactive_script()

    def test_docker_menu_invalid_input_handling(self):
        """Тест обработки неверного ввода в меню Docker"""
        mock_docker_service = Mock()

        with (
            patch(
                "app.interfaces.interactive.docker.DockerService",
                return_value=mock_docker_service,
            ),
            patch(
                "builtins.input", side_effect=["99", "0", "0"]
            ),  # Неверный ввод, затем выход, затем выход из главного меню
            patch("builtins.print"),
            patch("sys.exit"),  # Предотвращаем выход из системы
        ):
            try:
                docker.interactive_run()
            except SystemExit:
                pass  # Нормально, так как sys.exit замокан

            # Проверяем, что были вызваны методы установки/удаления в соответствии с правильным сценарием
            # В случае неверного ввода методы установки/удаления не должны вызываться
            mock_docker_service.install.assert_not_called()
            mock_docker_service.uninstall.assert_not_called()

    def test_interactive_menu_displays_info_correctly(self):
        """Тест отображения информации в интерактивных меню"""
        mock_docker_service = Mock()

        with (
            patch(
                "app.interfaces.interactive.docker.DockerService",
                return_value=mock_docker_service,
            ),
            patch(
                "builtins.input",
                side_effect=[
                    "00",  # Выбираем команду 00 для информации о Docker
                    "0",  # Нажимаем Enter для возврата в меню Docker
                    "0",  # Выходим из меню Docker
                    "0",  # Выходим из главного меню
                ],  # Выбираем команду 00, нажимаем Enter для возврата в меню, затем выходим
            ),  # Показываем информацию о Docker, затем выходим
            patch("builtins.print") as mock_print,
            patch("sys.exit"),  # Предотвращаем выход из системы
        ):
            mock_docker_service.get_info_lines.return_value = [
                "Docker info",
                "https://docker.com",
            ]
            try:
                docker.interactive_run()
            except SystemExit:
                pass  # Нормально, так как sys.exit замокан

            # Проверяем, что была выведена информация о Docker
            printed_texts = [
                call.args[0] for call in mock_print.call_args_list if call.args
            ]

            # Проверяем, что содержится информация о Docker
            docker_info_found = any(
                "Docker" in text for text in printed_texts if isinstance(text, str)
            )
            assert docker_info_found, "Information about Docker should be displayed"

            # Проверяем, что содержится ссылка на официальный сайт
            link_found = any(
                "https://docker.com" in text
                for text in printed_texts
                if isinstance(text, str)
            )
            assert link_found, "Official website link should be displayed"

    def test_traffic_guard_interactive_menu_install_flow(self):
        """Тест потока интерактивного меню TrafficGuard - установка"""
        # Мокаем сервис TrafficGuard
        mock_traffic_guard_service = Mock()

        with (
            patch(
                "app.interfaces.interactive.traffic_guard.TrafficGuardService",
                return_value=mock_traffic_guard_service,
            ),
            patch(
                "builtins.input", side_effect=["1", "0", "0"]
            ),  # Выбираем установку, затем выход, затем выход из главного меню
            patch("builtins.print"),
            patch("sys.exit"),  # Предотвращаем выход из системы
        ):
            # Вызываем интерактивный запуск TrafficGuard
            try:
                traffic_guard.interactive_run()
            except SystemExit:
                pass  # Нормально, так как sys.exit замокан

            # Проверяем, что был вызван метод установки
            mock_traffic_guard_service.install.assert_called_once()

    def test_traffic_guard_interactive_menu_uninstall_flow(self):
        """Тест потока интерактивного меню TrafficGuard - удаление"""
        # Мокаем сервис TrafficGuard
        mock_traffic_guard_service = Mock()

        with (
            patch(
                "app.interfaces.interactive.traffic_guard.TrafficGuardService",
                return_value=mock_traffic_guard_service,
            ),
            patch(
                "builtins.input", side_effect=["2", "0", "0"]
            ),  # Выбираем удаление, затем выход, затем выход из главного меню
            patch("builtins.print"),
            patch("sys.exit"),  # Предотвращаем выход из системы
        ):
            # Вызываем интерактивный запуск TrafficGuard
            try:
                traffic_guard.interactive_run()
            except SystemExit:
                pass  # Нормально, так как sys.exit замокан

            # Проверяем, что был вызван метод удаления
            mock_traffic_guard_service.uninstall.assert_called_once()

    def test_uv_interactive_menu_install_flow(self):
        """Тест потока интерактивного меню UV - установка"""
        # Мокаем сервис UV
        mock_uv_service = Mock()

        with (
            patch(
                "app.interfaces.interactive.uv.UVService", return_value=mock_uv_service
            ),
            patch(
                "builtins.input", side_effect=["1", "0", "0"]
            ),  # Выбираем установку, затем выход, затем выход из главного меню
            patch("builtins.print"),
            patch("sys.exit"),  # Предотвращаем выход из системы
        ):
            # Вызываем интерактивный запуск UV
            try:
                uv.interactive_run()
            except SystemExit:
                pass  # Нормально, так как sys.exit замокан

            # Проверяем, что был вызван метод установки
            mock_uv_service.install.assert_called_once()

    def test_uv_interactive_menu_uninstall_flow(self):
        """Тест потока интерактивного меню UV - удаление"""
        # Мокаем сервис UV
        mock_uv_service = Mock()

        with (
            patch(
                "app.interfaces.interactive.uv.UVService", return_value=mock_uv_service
            ),
            patch(
                "builtins.input", side_effect=["2", "0", "0"]
            ),  # Выбираем удаление, затем выход, затем выход из главного меню
            patch("builtins.print"),
            patch("sys.exit"),  # Предотвращаем выход из системы
        ):
            # Вызываем интерактивный запуск UV
            try:
                uv.interactive_run()
            except SystemExit:
                pass  # Нормально, так как sys.exit замокан

            # Проверяем, что был вызван метод удаления
            mock_uv_service.uninstall.assert_called_once()
