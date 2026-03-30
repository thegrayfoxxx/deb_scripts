from unittest.mock import Mock, patch

from app.interfaces.interactive import (
    bbr,
    docker,
    fail2ban,
    run,
    traffic_guard,
    ufw,
    uv,
)
from app.interfaces.interactive.menu_utils import MenuItem


def test_bbr_menu_displays_inline_status():
    service = Mock()
    service.is_installed.return_value = True

    with (
        patch("builtins.input", return_value="0") as mock_input,
        patch("builtins.print"),
    ):
        bbr.display_bbr_submenu(service)

    prompt = mock_input.call_args.args[0]
    assert "🟢 включен" in prompt
    assert "Показать статус BBR" in prompt


def test_docker_menu_displays_inline_status():
    service = Mock()
    service.is_installed.return_value = False

    with (
        patch("builtins.input", return_value="0") as mock_input,
        patch("builtins.print"),
    ):
        docker.display_docker_submenu(service)

    prompt = mock_input.call_args.args[0]
    assert "🔴 не установлен" in prompt
    assert "Показать статус Docker" in prompt


def test_fail2ban_menu_displays_inline_status():
    service = Mock()
    service.is_installed.return_value = True

    with (
        patch("builtins.input", return_value="0") as mock_input,
        patch("builtins.print"),
    ):
        fail2ban.display_fail2ban_submenu(service)

    prompt = mock_input.call_args.args[0]
    assert "🟢 установлен" in prompt
    assert "Показать статус Fail2Ban" in prompt


def test_trafficguard_menu_displays_inline_status():
    service = Mock()
    service.is_installed.return_value = False

    with (
        patch("builtins.input", return_value="0") as mock_input,
        patch("builtins.print"),
    ):
        traffic_guard.display_trafficguard_submenu(service)

    prompt = mock_input.call_args.args[0]
    assert "🔴 не установлен" in prompt
    assert "Показать статус TrafficGuard" in prompt


def test_uv_menu_displays_inline_status():
    service = Mock()
    service.is_installed.return_value = True

    with (
        patch("builtins.input", return_value="0") as mock_input,
        patch("builtins.print"),
    ):
        uv.display_uv_submenu(service)

    prompt = mock_input.call_args.args[0]
    assert "🟢 установлен" in prompt
    assert "Показать статус UV" in prompt


def test_ufw_menu_displays_inline_status():
    service = Mock()
    service.is_installed.return_value = True
    service.is_active.return_value = False

    with (
        patch("app.interfaces.interactive.ufw.UfwService", return_value=service),
        patch("builtins.input", return_value="0") as mock_input,
        patch("builtins.print"),
    ):
        ufw.show_ufw_menu()

    prompt = mock_input.call_args_list[0].args[0]
    assert "🟢 установлен" in prompt
    assert "🔴 выключен" in prompt


def test_main_menu_displays_inline_statuses():
    ufw_service = Mock()
    ufw_service.is_installed.return_value = True
    ufw_service.is_active.return_value = False

    bbr_service = Mock()
    bbr_service.is_active.return_value = True

    docker_service = Mock()
    docker_service.is_installed.return_value = False

    fail2ban_service = Mock()
    fail2ban_service.is_installed.return_value = True
    fail2ban_service.is_active.return_value = False

    tg_service = Mock()
    tg_service.is_installed.return_value = True
    tg_service.is_active.return_value = True

    uv_service = Mock()
    uv_service.is_installed.return_value = True

    menu_items = [
        MenuItem(
            key="1",
            label="1 - UFW",
            action=Mock(),
            status_renderer=lambda: "🔴 выключен",
        ),
        MenuItem(
            key="2",
            label="2 - BBR",
            action=Mock(),
            status_renderer=lambda: "🟢 включен",
        ),
        MenuItem(
            key="3",
            label="3 - Docker",
            action=Mock(),
            status_renderer=lambda: "🔴 не установлен",
        ),
        MenuItem(
            key="4",
            label="4 - Fail2Ban",
            action=Mock(),
            status_renderer=lambda: "🔴 не активен",
        ),
        MenuItem(
            key="5",
            label="5 - TrafficGuard",
            action=Mock(),
            status_renderer=lambda: "🟢 активен",
        ),
        MenuItem(
            key="6",
            label="6 - UV",
            action=Mock(),
            status_renderer=lambda: "🟢 установлен",
        ),
    ]

    with (
        patch(
            "app.interfaces.interactive.run.build_main_menu_items",
            return_value=menu_items,
        ),
        patch("builtins.input", return_value="0") as mock_input,
        patch("builtins.print"),
    ):
        run.display_main_menu()

    prompt = mock_input.call_args.args[0]
    assert "🔴 выключен" in prompt
    assert "🟢 включен" in prompt
    assert "🔴 не установлен" in prompt
    assert "🔴 не активен" in prompt
    assert "🟢 активен" in prompt
    assert "🟢 установлен" in prompt


def test_bbr_interactive_status_action_prints_service_status():
    service = Mock()
    service.is_installed.return_value = False
    service.get_status.return_value = "BBR: disabled"

    with (
        patch("app.interfaces.interactive.bbr.BBRService", return_value=service),
        patch("builtins.input", side_effect=["3", "0"]),
        patch("builtins.print") as mock_print,
    ):
        bbr.interactive_run()

    mock_print.assert_any_call("BBR: disabled")


def test_docker_interactive_status_action_prints_service_status():
    service = Mock()
    service.is_installed.return_value = True
    service.get_status.return_value = "Docker: installed"

    with (
        patch("app.interfaces.interactive.docker.DockerService", return_value=service),
        patch("builtins.input", side_effect=["3", "0"]),
        patch("builtins.print") as mock_print,
    ):
        docker.interactive_run()

    mock_print.assert_any_call("Docker: installed")


def test_fail2ban_interactive_status_action_prints_service_status():
    service = Mock()
    service.is_installed.return_value = True
    service.get_status.return_value = "Fail2Ban: installed"

    with (
        patch(
            "app.interfaces.interactive.fail2ban.Fail2BanService", return_value=service
        ),
        patch("builtins.input", side_effect=["3", "0"]),
        patch("builtins.print") as mock_print,
    ):
        fail2ban.interactive_run()

    mock_print.assert_any_call("Fail2Ban: installed")


def test_trafficguard_interactive_status_action_prints_service_status():
    service = Mock()
    service.is_installed.return_value = True
    service.get_status.return_value = "TrafficGuard: installed"

    with (
        patch(
            "app.interfaces.interactive.traffic_guard.TrafficGuardService",
            return_value=service,
        ),
        patch("builtins.input", side_effect=["3", "0"]),
        patch("builtins.print") as mock_print,
    ):
        traffic_guard.interactive_run()

    mock_print.assert_any_call("TrafficGuard: installed")


def test_uv_interactive_status_action_prints_service_status():
    service = Mock()
    service.is_installed.return_value = True
    service.get_status.return_value = "uv: installed"

    with (
        patch("app.interfaces.interactive.uv.UVService", return_value=service),
        patch("builtins.input", side_effect=["3", "0"]),
        patch("builtins.print") as mock_print,
    ):
        uv.interactive_run()

    mock_print.assert_any_call("uv: installed")


def test_ufw_interactive_status_action_prints_service_status():
    service = Mock()
    service.is_installed.return_value = True
    service.is_active.return_value = True
    service.get_status.return_value = "Status: active"

    with (
        patch("app.interfaces.interactive.ufw.UfwService", return_value=service),
        patch("builtins.input", side_effect=["4", "0"]),
        patch("builtins.print") as mock_print,
    ):
        ufw.show_ufw_menu()

    mock_print.assert_any_call("Status: active")
