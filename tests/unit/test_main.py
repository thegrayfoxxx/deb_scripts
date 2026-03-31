from types import SimpleNamespace
from unittest.mock import patch

import main


def test_main_updates_system_before_interactive_mode():
    args = SimpleNamespace(
        log_level="info",
        install=None,
        uninstall=None,
        activate=None,
        deactivate=None,
        status=None,
        info=None,
        all=False,
    )

    with (
        patch("main.check_root") as mock_check_root,
        patch("main.update_os") as mock_update_os,
        patch("main.run_interactive_script") as mock_interactive,
        patch("main.parse_args", return_value=args),
        patch("main.set_default_console_level") as mock_set_level,
    ):
        result = main.main()

    assert result == 0
    mock_set_level.assert_called_once_with("info")
    mock_check_root.assert_called_once()
    mock_update_os.assert_called_once()
    mock_interactive.assert_called_once()


def test_main_updates_system_before_non_interactive_mode():
    args = SimpleNamespace(
        log_level="info",
        install=["3"],
        uninstall=None,
        activate=None,
        deactivate=None,
        status=None,
        info=None,
        all=False,
    )

    with (
        patch("main.check_root") as mock_check_root,
        patch("main.update_os") as mock_update_os,
        patch("main.run_non_interactive_commands", return_value=True) as mock_non_interactive,
        patch("main.parse_args", return_value=args),
        patch("main.set_default_console_level") as mock_set_level,
    ):
        result = main.main()

    assert result == 0
    mock_set_level.assert_called_once_with("info")
    mock_check_root.assert_called_once()
    mock_update_os.assert_called_once()
    mock_non_interactive.assert_called_once_with(args)


def test_main_returns_non_zero_when_non_interactive_operation_fails():
    args = SimpleNamespace(
        log_level="info",
        install=["3"],
        uninstall=None,
        activate=None,
        deactivate=None,
        status=None,
        info=None,
        all=False,
    )

    with (
        patch("main.check_root") as mock_check_root,
        patch("main.update_os") as mock_update_os,
        patch("main.run_non_interactive_commands", return_value=False) as mock_non_interactive,
        patch("main.parse_args", return_value=args),
        patch("main.set_default_console_level") as mock_set_level,
    ):
        result = main.main()

    assert result == 1
    mock_set_level.assert_called_once_with("info")
    mock_check_root.assert_called_once()
    mock_update_os.assert_called_once()
    mock_non_interactive.assert_called_once_with(args)


def test_main_treats_status_request_as_non_interactive_mode():
    args = SimpleNamespace(
        log_level="info",
        install=None,
        uninstall=None,
        activate=None,
        deactivate=None,
        status=["1"],
        info=None,
        all=False,
    )

    with (
        patch("main.check_root") as mock_check_root,
        patch("main.update_os") as mock_update_os,
        patch("main.run_non_interactive_commands", return_value=True) as mock_non_interactive,
        patch("main.run_interactive_script") as mock_interactive,
        patch("main.parse_args", return_value=args),
        patch("main.set_default_console_level") as mock_set_level,
    ):
        result = main.main()

    assert result == 0
    mock_set_level.assert_called_once_with("info")
    mock_check_root.assert_called_once()
    mock_update_os.assert_called_once()
    mock_non_interactive.assert_called_once_with(args)
    mock_interactive.assert_not_called()


def test_has_non_interactive_request_detects_all_mode_flags():
    args = SimpleNamespace(
        install=None,
        uninstall=None,
        activate=None,
        deactivate=None,
        status=[],
        info=None,
        all=True,
    )

    assert main._has_non_interactive_request(args) is True


def test_main_treats_status_all_request_as_non_interactive_mode():
    args = SimpleNamespace(
        log_level="info",
        install=None,
        uninstall=None,
        activate=None,
        deactivate=None,
        status=[],
        info=None,
        all=True,
    )

    with (
        patch("main.check_root") as mock_check_root,
        patch("main.update_os") as mock_update_os,
        patch("main.run_non_interactive_commands", return_value=True) as mock_non_interactive,
        patch("main.run_interactive_script") as mock_interactive,
        patch("main.parse_args", return_value=args),
        patch("main.set_default_console_level") as mock_set_level,
    ):
        result = main.main()

    assert result == 0
    mock_set_level.assert_called_once_with("info")
    mock_check_root.assert_called_once()
    mock_update_os.assert_called_once()
    mock_non_interactive.assert_called_once_with(args)
    mock_interactive.assert_not_called()


def test_run_cli_returns_130_on_keyboard_interrupt():
    with patch("main.main", side_effect=KeyboardInterrupt), patch("main.logger") as mock_logger:
        result = main.run_cli()

    assert result == 130
    mock_logger.info.assert_called_once_with("👋 Выход...")


def test_run_cli_returns_1_on_permission_error():
    with patch("main.main", side_effect=PermissionError), patch("main.logger") as mock_logger:
        result = main.run_cli()

    assert result == 1
    mock_logger.error.assert_called_once_with(
        "🔐 Недостаточно прав для выполнения операции. Запустите скрипт с правами суперпользователя. (sudo)"
    )
