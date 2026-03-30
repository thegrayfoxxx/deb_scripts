from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.interfaces.cli.non_interactive import run_non_interactive_commands


def _make_args(*, install=None, uninstall=None):
    return SimpleNamespace(install=install, uninstall=uninstall)


def _make_entry(service_instance):
    return SimpleNamespace(service_factory=MagicMock(return_value=service_instance))


def test_run_non_interactive_install_uses_registry_service_factory():
    service = MagicMock()

    with patch(
        "app.interfaces.cli.non_interactive.get_service_entry",
        return_value=_make_entry(service),
    ) as mock_get_entry:
        result = run_non_interactive_commands(_make_args(install=["2"]))

    assert result is True
    mock_get_entry.assert_called_once_with("2")
    service.install.assert_called_once()


def test_run_non_interactive_uninstall_uses_registry_service_factory():
    service = MagicMock()

    with patch(
        "app.interfaces.cli.non_interactive.get_service_entry",
        return_value=_make_entry(service),
    ) as mock_get_entry:
        result = run_non_interactive_commands(_make_args(uninstall=["4"]))

    assert result is True
    mock_get_entry.assert_called_once_with("4")
    service.uninstall.assert_called_once()


def test_run_non_interactive_mixed_operations():
    install_service = MagicMock()
    uninstall_service = MagicMock()
    entries = {
        "2": _make_entry(install_service),
        "3": _make_entry(uninstall_service),
    }

    with patch(
        "app.interfaces.cli.non_interactive.get_service_entry",
        side_effect=lambda code: entries.get(code),
    ):
        result = run_non_interactive_commands(
            _make_args(install=["2"], uninstall=["3"])
        )

    assert result is True
    install_service.install.assert_called_once()
    uninstall_service.uninstall.assert_called_once()


def test_run_non_interactive_invalid_service_code_install():
    with (
        patch(
            "app.interfaces.cli.non_interactive.get_service_entry", return_value=None
        ),
        patch("app.interfaces.cli.non_interactive.logger") as mock_logger,
    ):
        result = run_non_interactive_commands(_make_args(install=["99"]))

    assert result is False
    mock_logger.error.assert_called_once_with(
        "❌ Неизвестный код сервиса для установки: 99"
    )


def test_run_non_interactive_invalid_service_code_uninstall():
    with (
        patch(
            "app.interfaces.cli.non_interactive.get_service_entry", return_value=None
        ),
        patch("app.interfaces.cli.non_interactive.logger") as mock_logger,
    ):
        result = run_non_interactive_commands(_make_args(uninstall=["99"]))

    assert result is False
    mock_logger.error.assert_called_once_with(
        "❌ Неизвестный код сервиса для удаления: 99"
    )


def test_run_non_interactive_returns_false_when_service_returns_false():
    service = MagicMock()
    service.install.return_value = False

    with patch(
        "app.interfaces.cli.non_interactive.get_service_entry",
        return_value=_make_entry(service),
    ):
        result = run_non_interactive_commands(_make_args(install=["1"]))

    assert result is False
    service.install.assert_called_once()


def test_run_non_interactive_no_operations():
    result = run_non_interactive_commands(_make_args())
    assert result is True


def test_run_non_interactive_processes_all_requested_services():
    services = {code: MagicMock() for code in ["1", "2", "3", "4", "5", "6"]}
    entries = {code: _make_entry(service) for code, service in services.items()}

    with patch(
        "app.interfaces.cli.non_interactive.get_service_entry",
        side_effect=lambda code: entries.get(code),
    ):
        result = run_non_interactive_commands(_make_args(install=list(services)))

    assert result is True
    for service in services.values():
        service.install.assert_called_once()


def test_run_non_interactive_install_and_uninstall_same_service():
    service = MagicMock()

    with patch(
        "app.interfaces.cli.non_interactive.get_service_entry",
        return_value=_make_entry(service),
    ):
        result = run_non_interactive_commands(
            _make_args(install=["2"], uninstall=["2"])
        )

    assert result is True
    service.install.assert_called_once()
    service.uninstall.assert_called_once()
