from types import SimpleNamespace
from unittest.mock import patch

import main


def test_main_updates_system_before_interactive_mode():
    with (
        patch("main.check_root") as mock_check_root,
        patch("main.update_os") as mock_update_os,
        patch("main.run_interactive_script") as mock_interactive,
        patch.object(main, "app_args", SimpleNamespace(install=None, uninstall=None)),
    ):
        result = main.main()

    assert result == 0
    mock_check_root.assert_called_once()
    mock_update_os.assert_called_once()
    mock_interactive.assert_called_once()


def test_main_updates_system_before_non_interactive_mode():
    args = SimpleNamespace(install=["3"], uninstall=None)

    with (
        patch("main.check_root") as mock_check_root,
        patch("main.update_os") as mock_update_os,
        patch("main.run_non_interactive_commands", return_value=True) as mock_non_interactive,
        patch.object(main, "app_args", args),
    ):
        result = main.main()

    assert result == 0
    mock_check_root.assert_called_once()
    mock_update_os.assert_called_once()
    mock_non_interactive.assert_called_once_with(args)


def test_main_returns_non_zero_when_non_interactive_operation_fails():
    args = SimpleNamespace(install=["3"], uninstall=None)

    with (
        patch("main.check_root") as mock_check_root,
        patch("main.update_os") as mock_update_os,
        patch("main.run_non_interactive_commands", return_value=False) as mock_non_interactive,
        patch.object(main, "app_args", args),
    ):
        result = main.main()

    assert result == 1
    mock_check_root.assert_called_once()
    mock_update_os.assert_called_once()
    mock_non_interactive.assert_called_once_with(args)


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
