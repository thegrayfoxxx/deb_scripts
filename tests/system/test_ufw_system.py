"""Системные тесты для проверки работы UFW сервиса в реальной системной среде"""

from unittest.mock import patch

import pytest

from app.services.ufw import UfwService


@pytest.mark.system
class TestUfwSystemService:
    """Системные тесты для проверки работы UFW в реальной среде (только в Docker-контейнере)"""

    def setup_method(self):
        self.service = UfwService()

    @pytest.mark.skipif(
        True, reason="Пропускаем системные тесты UFW в CI/CD, так как требуют привилегий"
    )
    def test_full_ufw_lifecycle_in_container(self):
        """Проверка полного жизненного цикла UFW в изолированной среде"""
        # В реальном тесте в Docker-контейнере:
        # 1. Устанавливаем UFW
        result = self.service.install()
        assert result is True

        # 2. Проверяем установку
        assert self.service.is_installed() is True

        # 3. Добавляем несколько правил
        assert self.service.open_common_ports() is True

        # 4. Включаем фаервол
        assert self.service.enable_with_ssh_only() is True

        # 5. Проверяем статус
        status = self.service.get_status()
        assert "active" in status.lower()

        # 6. Отключаем
        assert self.service.disable() is True

        # 7. Сбрасываем
        assert self.service.reset() is True

        # 8. Удаляем
        # with patch('builtins.input', return_value='YES'):  # Подтверждение удаления
        #     result = self.service.uninstall()
        #     assert result is True

    def test_ufw_service_basic_functionality_mocked(self):
        """Тест основной функциональности UFW с моками для безопасного тестирования"""
        # Тестируем логику работы без реальных изменений в системе

        # Тестируем проверку установки
        with patch("app.services.ufw.run") as mock_run:
            from unittest.mock import Mock

            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "/usr/sbin/ufw"
            mock_run.return_value = mock_result

            self.service.is_installed()
            # Проверяем, что вызывается правильная команда
            mock_run.assert_called_once_with(["which", "ufw"], check=False)

    def test_ufw_install_already_present(self):
        """Тест установки UFW когда он уже установлен"""
        with patch.object(self.service, "is_installed", return_value=True):
            with patch.object(self.service, "ensure_safe_baseline") as mock_safe_baseline:
                mock_safe_baseline.return_value = True
                result = self.service.install()

                assert result is True
                mock_safe_baseline.assert_called_once()

    def test_ufw_install_requires_root(self):
        """Тест что установка UFW требует root прав"""
        with patch("os.geteuid", return_value=1000):  # обычный пользователь
            result = self.service.install()
            assert result is False

    def test_ufw_methods_resilience(self):
        """Тест устойчивости методов UFW к сбоям внешних команд"""
        # Тестирование корректной обработки ошибок

        # Тестируем метод получения статуса при ошибке
        with patch("app.services.ufw.run") as mock_run:
            from unittest.mock import Mock

            mock_result = Mock()
            mock_result.returncode = 1  # Ошибка
            mock_result.stdout = ""
            mock_run.return_value = mock_result

            status = self.service.get_status()
            assert "Статус установки: 🔴 не установлен" in status
            assert "Статус активации: 🔴 не активирован" in status
            assert "Вывод ufw status: недоступен" in status

    @pytest.mark.integration
    def test_ufw_service_compatibility_with_traffic_guard(self):
        """Тест совместимости UFW сервиса с TrafficGuard (проверяем, что TrafficGuard использует наш UFW сервис)"""
        from app.services.traffic_guard import TrafficGuardService

        tg_service = TrafficGuardService()

        # Проверяем, что в TrafficGuard используется наш UfwService
        # для этого анализируем метод _setup_firewall_safety
        import inspect

        source_code = inspect.getsource(tg_service._setup_firewall_safety)

        # В обновленном TrafficGuard должен использоваться UfwService
        assert (
            "UfwService()" in source_code
            or "ufw_service" in source_code
            or "app.services.ufw" in source_code
        )

    def test_ufw_service_idempotency(self):
        """Тест идемпотентности операций UFW сервиса"""
        # Тестирование того, что повторные вызовы одних и тех же операций
        # не приводят к ошибкам и дают одинаковый результат

        # Устанавливаем моки для предотвращения реальных изменений
        with patch("os.geteuid", return_value=0):  # root
            with patch("app.services.ufw.run") as mock_run:

                def run_side_effect(cmd, **kwargs):
                    from unittest.mock import Mock

                    result = Mock()
                    if cmd == ["which", "ufw"]:
                        result.returncode = 0
                        result.stdout = "/usr/sbin/ufw"
                    elif isinstance(cmd, list) and cmd[0] == "ufw":
                        result.returncode = 0
                        result.stdout = ""
                    else:
                        result.returncode = 0
                        result.stdout = ""
                    return result

                mock_run.side_effect = run_side_effect

                # Проверяем, что установка идемпотентна
                result1 = self.service.install()
                result2 = self.service.install()

                assert result1 == result2
                # Должно быть 2 вызова is_installed() (по одному на каждую установку)
                # + вызовы для других операций
