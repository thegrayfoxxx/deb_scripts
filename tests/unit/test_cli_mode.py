from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.interfaces.cli.non_interactive import run_non_interactive_commands


def _make_args(
    *,
    install=None,
    uninstall=None,
    activate=None,
    deactivate=None,
    status=None,
    info=None,
    all=False,
):
    return SimpleNamespace(
        install=install,
        uninstall=uninstall,
        activate=activate,
        deactivate=deactivate,
        status=status,
        info=info,
        all=all,
    )


def _make_entry(service_instance, *, name="Demo"):
    return SimpleNamespace(name=name, service_factory=MagicMock(return_value=service_instance))


def _make_activatable_service():
    return MagicMock(
        spec=[
            "install",
            "uninstall",
            "is_installed",
            "get_status",
            "get_info_lines",
            "activate",
            "deactivate",
            "is_active",
        ]
    )


def test_run_non_interactive_install_uses_registry_service_factory():
    service = MagicMock()

    with (
        patch(
            "app.interfaces.cli.non_interactive.get_service_entry",
            return_value=_make_entry(service, name="BBR"),
        ) as mock_get_entry,
        patch("builtins.print") as mock_print,
    ):
        result = run_non_interactive_commands(_make_args(install=["2"]))

    assert result is True
    mock_get_entry.assert_called_once_with("2")
    service.install.assert_called_once()
    mock_print.assert_any_call("✅ [BBR] install")


def test_run_non_interactive_uninstall_uses_registry_service_factory():
    service = MagicMock()

    with (
        patch(
            "app.interfaces.cli.non_interactive.get_service_entry",
            return_value=_make_entry(service, name="Fail2Ban"),
        ) as mock_get_entry,
        patch("builtins.print") as mock_print,
    ):
        result = run_non_interactive_commands(_make_args(uninstall=["4"]))

    assert result is True
    mock_get_entry.assert_called_once_with("4")
    service.uninstall.assert_called_once_with(confirm=False)
    mock_print.assert_any_call("✅ [Fail2Ban] uninstall")


def test_run_non_interactive_activate_uses_service_activate():
    service = _make_activatable_service()
    service.activate.return_value = True

    with (
        patch(
            "app.interfaces.cli.non_interactive.get_service_entry",
            return_value=_make_entry(service, name="UFW"),
        ),
        patch("builtins.print") as mock_print,
    ):
        result = run_non_interactive_commands(_make_args(activate=["1"]))

    assert result is True
    service.activate.assert_called_once()
    mock_print.assert_any_call("✅ [UFW] activate")


def test_run_non_interactive_deactivate_uses_service_deactivate():
    service = _make_activatable_service()
    service.deactivate.return_value = True

    with (
        patch(
            "app.interfaces.cli.non_interactive.get_service_entry",
            return_value=_make_entry(service, name="Fail2Ban"),
        ),
        patch("builtins.print") as mock_print,
    ):
        result = run_non_interactive_commands(_make_args(deactivate=["4"]))

    assert result is True
    service.deactivate.assert_called_once_with(confirm=False)
    mock_print.assert_any_call("✅ [Fail2Ban] deactivate")


def test_run_non_interactive_status_prints_service_status():
    service = MagicMock()
    service.get_status.return_value = "demo status"

    with (
        patch(
            "app.interfaces.cli.non_interactive.get_service_entry",
            return_value=_make_entry(service, name="Docker"),
        ),
        patch("builtins.print") as mock_print,
    ):
        result = run_non_interactive_commands(_make_args(status=["3"]))

    assert result is True
    mock_print.assert_any_call("[Docker]")
    mock_print.assert_any_call("demo status")


def test_run_non_interactive_info_prints_service_info_lines():
    service = MagicMock()
    service.get_info_lines.return_value = ("line 1", "line 2")

    with (
        patch(
            "app.interfaces.cli.non_interactive.get_service_entry",
            return_value=_make_entry(service, name="UV"),
        ),
        patch("builtins.print") as mock_print,
    ):
        result = run_non_interactive_commands(_make_args(info=["6"]))

    assert result is True
    mock_print.assert_any_call("[UV]")
    mock_print.assert_any_call("line 1")
    mock_print.assert_any_call("line 2")


def test_run_non_interactive_returns_false_for_activate_on_non_activatable_service():
    service = MagicMock(
        spec=["install", "uninstall", "is_installed", "get_status", "get_info_lines"]
    )

    with (
        patch(
            "app.interfaces.cli.non_interactive.get_service_entry",
            return_value=_make_entry(service, name="Docker"),
        ),
        patch("app.interfaces.cli.non_interactive.logger") as mock_logger,
    ):
        result = run_non_interactive_commands(_make_args(activate=["3"]))

    assert result is False
    mock_logger.error.assert_called_once_with("❌ Сервис Docker не поддерживает активацию")


def test_run_non_interactive_returns_false_for_deactivate_on_non_activatable_service():
    service = MagicMock(
        spec=["install", "uninstall", "is_installed", "get_status", "get_info_lines"]
    )

    with (
        patch(
            "app.interfaces.cli.non_interactive.get_service_entry",
            return_value=_make_entry(service, name="UV"),
        ),
        patch("app.interfaces.cli.non_interactive.logger") as mock_logger,
    ):
        result = run_non_interactive_commands(_make_args(deactivate=["6"]))

    assert result is False
    mock_logger.error.assert_called_once_with("❌ Сервис UV не поддерживает отключение")


def test_run_non_interactive_invalid_service_code_install():
    with (
        patch("app.interfaces.cli.non_interactive.get_service_entry", return_value=None),
        patch("app.interfaces.cli.non_interactive.logger") as mock_logger,
    ):
        result = run_non_interactive_commands(_make_args(install=["99"]))

    assert result is False
    mock_logger.error.assert_called_once_with(
        "❌ Неизвестный код сервиса для операции 'install': 99"
    )


def test_run_non_interactive_returns_false_when_service_returns_false():
    service = MagicMock()
    service.install.return_value = False

    with (
        patch(
            "app.interfaces.cli.non_interactive.get_service_entry",
            return_value=_make_entry(service, name="UFW"),
        ),
        patch("builtins.print") as mock_print,
    ):
        result = run_non_interactive_commands(_make_args(install=["1"]))

    assert result is False
    service.install.assert_called_once()
    mock_print.assert_any_call("❌ [UFW] install")


def test_run_non_interactive_no_operations():
    result = run_non_interactive_commands(_make_args())
    assert result is True


def test_run_non_interactive_processes_all_requested_operations():
    service = _make_activatable_service()
    service.activate.return_value = True
    service.deactivate.return_value = True
    service.get_status.return_value = "ok"
    service.get_info_lines.return_value = ("info",)

    with (
        patch(
            "app.interfaces.cli.non_interactive.get_service_entry",
            return_value=_make_entry(service, name="UFW"),
        ),
        patch("builtins.print") as mock_print,
    ):
        result = run_non_interactive_commands(
            _make_args(
                install=["1"],
                activate=["1"],
                status=["1"],
                info=["1"],
                deactivate=["1"],
                uninstall=["1"],
            )
        )

    assert result is True
    service.install.assert_called_once()
    service.activate.assert_called_once()
    service.deactivate.assert_called_once_with(confirm=False)
    service.uninstall.assert_called_once_with(confirm=False)
    mock_print.assert_any_call("✅ [UFW] install")
    mock_print.assert_any_call("✅ [UFW] activate")
    mock_print.assert_any_call("✅ [UFW] deactivate")
    mock_print.assert_any_call("✅ [UFW] uninstall")


def test_run_non_interactive_uses_all_service_codes_when_all_flag_is_set():
    service = _make_activatable_service()
    service.get_status.return_value = "ok"

    with (
        patch(
            "app.interfaces.cli.non_interactive.get_all_service_codes",
            return_value=["1", "2", "3"],
        ),
        patch(
            "app.interfaces.cli.non_interactive.get_service_entry",
            return_value=_make_entry(service, name="Demo"),
        ) as mock_get_entry,
        patch("builtins.print"),
    ):
        result = run_non_interactive_commands(_make_args(status=[], all=True))

    assert result is True
    assert [call.args[0] for call in mock_get_entry.call_args_list] == ["1", "2", "3"]
