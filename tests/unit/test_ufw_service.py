from unittest.mock import Mock, patch

from app.services.ufw import UfwService


class TestUfwService:
    def setup_method(self):
        self.service = UfwService()

    def test_ensure_default_policies_returns_false_on_command_failure(self):
        with patch("app.services.ufw.run") as mock_run:
            mock_run.side_effect = [
                Mock(returncode=1, stdout=""),
                Mock(returncode=0, stdout=""),
            ]

            result = self.service._ensure_default_policies()

        assert result is False

    def test_ensure_default_policies_returns_false_on_exception(self):
        with patch("app.services.ufw.run", side_effect=RuntimeError("boom")):
            assert self.service._ensure_default_policies() is False

    def test_ensure_safe_baseline_returns_false_when_default_policies_fail(self):
        with patch.object(self.service, "_ensure_default_policies", return_value=False):
            assert self.service.ensure_safe_baseline() is False

    def test_ensure_safe_baseline_returns_false_when_ssh_rule_fails(self):
        with (
            patch.object(self.service, "_ensure_default_policies", return_value=True),
            patch.object(self.service, "_ensure_ssh_allowed", return_value=False),
        ):
            assert self.service.ensure_safe_baseline() is False

    @patch("app.services.ufw.run")
    def test_is_installed_true(self, mock_run):
        """Test that is_installed returns True when UFW is available."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        assert self.service.is_installed() is True
        mock_run.assert_called_once_with(["which", "ufw"], check=False)

    @patch("app.services.ufw.run")
    def test_is_installed_false(self, mock_run):
        """Test that is_installed returns False when UFW is not available."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        assert self.service.is_installed() is False

    @patch("os.geteuid", return_value=1000)  # Non-root
    def test_install_no_root_privileges(self, mock_geteuid):
        """Test that install fails without root privileges."""
        with patch("app.bootstrap.logger.get_logger"):
            result = self.service.install()
            assert result is False

    @patch("os.geteuid", return_value=0)  # Root privileges
    @patch("app.core.subprocess.run")
    def test_install_already_installed(self, mock_run, mock_geteuid):
        """Test that install succeeds when UFW is already installed."""
        # Mock is_installed to return True
        with patch.object(self.service, "is_installed", return_value=True):
            with patch.object(self.service, "ensure_safe_baseline") as mock_safe_baseline:
                mock_safe_baseline.return_value = True
                result = self.service.install()

                assert result is True
                mock_safe_baseline.assert_called_once()

    @patch("os.geteuid", return_value=0)  # Root privileges
    @patch("app.services.ufw.run")
    def test_install_success(self, mock_run, mock_geteuid):
        """Test successful UFW installation."""

        def side_effect(cmd, check=True, **kwargs):
            if cmd == ["which", "ufw"]:
                result = Mock()
                result.returncode = 1  # Not installed initially
                return result
            elif isinstance(cmd, list) and cmd[0] == "apt":
                result = Mock()
                result.returncode = 0  # Installation succeeds
                result.stdout = ""
                return result
            elif isinstance(cmd, list) and len(cmd) >= 2 and cmd[0] == "ufw":
                result = Mock()
                result.returncode = 0
                result.stdout = ""
                return result
            else:
                result = Mock()
                result.returncode = 0
                result.stdout = ""
                return result

        mock_run.side_effect = side_effect

        # Mock is_installed to return False initially, then True
        call_state = {"count": 0}

        def mock_is_installed():
            call_state["count"] += 1
            # Return False on first call (before install), True on subsequent calls
            return call_state["count"] > 1

        with patch.object(self.service, "is_installed", side_effect=mock_is_installed):
            result = self.service.install()

            assert result is True
            # Check that apt install was called
            install_calls = [
                call for call in mock_run.call_args_list if call[0][0] and call[0][0][0] == "apt"
            ]
            assert len([c for c in install_calls if "ufw" in c[0][0]]) >= 1

    @patch("os.geteuid", return_value=0)  # Root privileges
    @patch("app.services.ufw.run")
    def test_install_failure(self, mock_run, mock_geteuid):
        """Test UFW installation failure."""

        def side_effect(cmd, check=True, **kwargs):
            if cmd == ["which", "ufw"]:
                result = Mock()
                result.returncode = 1  # Not installed
                return result
            elif (
                isinstance(cmd, list) and "ufw" in cmd and cmd[0] == "apt" and cmd[1] == "install"
            ):
                result = Mock()
                result.returncode = 1  # Installation failed
                result.stdout = ""
                result.stderr = "Failed to install ufw"
                return result
            elif isinstance(cmd, list) and len(cmd) >= 2 and cmd[0] == "ufw":
                result = Mock()
                result.returncode = 0
                result.stdout = ""
                return result
            else:
                result = Mock()
                result.returncode = 0
                result.stdout = ""
                return result

        mock_run.side_effect = side_effect

        # Mock is_installed to return False initially, then still False after attempted install
        call_state = {"count": 0}

        def mock_is_installed():
            call_state["count"] += 1
            # Return False both before and after attempted install
            return False

        with patch.object(self.service, "is_installed", side_effect=mock_is_installed):
            result = self.service.install()
            assert result is False

    @patch("app.services.ufw.run")
    def test_ensure_ssh_allowed_already_exists(self, mock_run):
        """Test _ensure_ssh_allowed when SSH rule already exists."""

        def side_effect(cmd, check=True, **kwargs):
            result = Mock()
            if cmd == ["ufw", "show", "added"]:
                result.stdout = "22/tcp                    ALLOW IN    Anywhere on eth0"
                result.returncode = 0
            else:
                result.stdout = ""
                result.returncode = 0
            return result

        mock_run.side_effect = side_effect

        result = self.service._ensure_ssh_allowed()
        assert result is True
        # Should check for existing rules
        assert mock_run.called

    @patch("app.services.ufw.run")
    def test_ensure_ssh_allowed_exception_handling(self, mock_run):
        """Test _ensure_ssh_allowed handles exceptions properly."""

        def side_effect(cmd, check=True, **kwargs):
            # Raise an exception to test exception handling
            raise RuntimeError("Test exception")

        mock_run.side_effect = side_effect

        result = self.service._ensure_ssh_allowed()
        assert result is False  # Should return False on exception

    @patch("app.services.ufw.run")
    def test_get_status_exception_handling(self, mock_run):
        """Test get_status handles exceptions properly."""

        def side_effect(cmd, check=True, **kwargs):
            # Raise an exception to test exception handling
            raise RuntimeError("Test exception")

        mock_run.side_effect = side_effect

        result = self.service.get_status()
        assert "Статус установки: 🔴 не установлен" in result
        assert "Статус активации: 🔴 не активирован" in result
        assert "Вывод ufw status: ошибка получения статуса" in result

    @patch("os.geteuid", return_value=1000)  # Non-root
    @patch("app.services.ufw.run")
    def test_install_without_root_privileges(self, mock_run, mock_geteuid):
        """Test install fails when not running as root."""
        result = self.service.install()
        assert result is False

    @patch("app.services.ufw.run")
    def test_uninstall_package_removal_failure(self, mock_run):
        """Test uninstall when package removal fails."""

        def side_effect(cmd, check=True, **kwargs):
            result = Mock()
            if cmd == ["which", "ufw"]:
                result.returncode = 0  # UFW is installed
            elif isinstance(cmd, list) and cmd[0] == "apt" and "remove" in cmd:
                result.returncode = 1  # Removal fails
            elif isinstance(cmd, list) and cmd[0] == "bash":
                result.returncode = 0  # reset command works
            else:
                result.returncode = 0
            result.stdout = ""
            return result

        mock_run.side_effect = side_effect

        with patch.object(self.service, "is_installed", return_value=True):
            result = self.service.uninstall()
            assert result is False

    @patch("app.services.ufw.run")
    def test_disable_when_not_installed(self, mock_run):
        """Test disable when UFW is not installed."""

        with patch.object(self.service, "is_installed", return_value=False):
            result = self.service.reset()
            assert result is True  # Should return True as nothing to reset

    @patch("builtins.input", return_value="n")
    def test_disable_cancelled_by_user(self, mock_input):
        assert self.service.disable(confirm=True) is False

    @patch("builtins.input", return_value="n")
    def test_reset_cancelled_by_user(self, mock_input):
        assert self.service.reset(confirm=True) is False

    @patch("builtins.input", return_value="n")
    def test_uninstall_cancelled_by_user(self, mock_input):
        assert self.service.uninstall(confirm=True) is False

    @patch("app.services.ufw.run")
    def test_uninstall_when_not_installed(self, mock_run):
        """Test uninstall when UFW is not installed."""

        with patch.object(self.service, "is_installed", return_value=False):
            result = self.service.uninstall()
            assert result is True  # Should return True as nothing to uninstall

    def test_open_common_ports_returns_false_when_all_ports_fail(self):
        with patch("app.services.ufw.run", return_value=Mock(returncode=1, stdout="")):
            assert self.service.open_common_ports() is False

    @patch("app.services.ufw.run", return_value=Mock(returncode=0, stdout=""))
    def test_close_port_success(self, mock_run):
        assert self.service.close_port("8080") is True
        mock_run.assert_called_once_with(["ufw", "delete", "allow", "8080"], check=False)

    @patch("app.services.ufw.run", return_value=Mock(returncode=1, stdout=""))
    def test_close_port_failure(self, mock_run):
        assert self.service.close_port("8080") is False

    @patch("app.services.ufw.run")
    def test_close_port_rejects_ssh_rule(self, mock_run):
        assert self.service.close_port("22") is False
        mock_run.assert_not_called()

    @patch("app.services.ufw.os.geteuid", return_value=0)  # Root privileges
    @patch("app.services.ufw.run")
    def test_install_exception_handling(self, mock_run, mock_geteuid):
        """Test install handles exceptions properly."""

        def side_effect(cmd, check=True, **kwargs):
            # Raise an exception to test exception handling
            raise RuntimeError("Test exception")

        mock_run.side_effect = side_effect

        result = self.service.install()
        assert result is False  # Should return False on exception

    @patch("app.services.ufw.os.geteuid", return_value=0)  # Root privileges
    @patch("app.services.ufw.run")
    def test_install_permission_error(self, mock_run, mock_geteuid):
        """Test install handles permission errors properly."""

        def side_effect(cmd, check=True, **kwargs):
            # Raise a PermissionError
            raise PermissionError("Test permission error")

        mock_run.side_effect = side_effect

        result = self.service.install()
        assert result is False  # Should return False on permission error

    @patch("app.services.ufw.run")
    def test_enable_with_ssh_only_exception_handling(self, mock_run):
        """Test enable_with_ssh_only handles exceptions properly."""

        def side_effect(cmd, check=True, **kwargs):
            # Raise an exception to test exception handling
            raise RuntimeError("Test exception")

        mock_run.side_effect = side_effect

        result = self.service.enable_with_ssh_only()
        assert result is False  # Should return False on exception

    @patch("app.services.ufw.run")
    def test_open_common_ports_exception_handling(self, mock_run):
        """Test open_common_ports handles exceptions properly."""

        def side_effect(cmd, check=True, **kwargs):
            # Raise an exception to test exception handling
            raise RuntimeError("Test exception")

        mock_run.side_effect = side_effect

        result = self.service.open_common_ports()
        assert result is False  # Should return False on exception

    @patch("app.services.ufw.run")
    def test_disable_exception_handling(self, mock_run):
        """Test disable handles exceptions properly."""

        def side_effect(cmd, check=True, **kwargs):
            # Raise an exception to test exception handling
            raise RuntimeError("Test exception")

        mock_run.side_effect = side_effect

        with patch.object(self.service, "_is_installed", return_value=True):
            # Also patch _is_active to avoid exception during status check
            with patch.object(self.service, "_is_active", return_value=True):
                result = self.service.disable()
                assert result is False  # Should return False on exception

    @patch("app.services.ufw.run")
    def test_reset_exception_handling(self, mock_run):
        """Test reset handles exceptions properly."""

        def side_effect(cmd, check=True, **kwargs):
            # Raise an exception to test exception handling
            raise RuntimeError("Test exception")

        mock_run.side_effect = side_effect

        with patch.object(self.service, "_is_installed", return_value=True):
            result = self.service.reset()
            assert result is False  # Should return False on exception

    @patch("app.services.ufw.run")
    def test_uninstall_exception_handling(self, mock_run):
        """Test uninstall handles exceptions properly."""

        def side_effect(cmd, check=True, **kwargs):
            # Raise an exception to test exception handling
            raise RuntimeError("Test exception")

        mock_run.side_effect = side_effect

        with patch.object(self.service, "_is_installed", return_value=True):
            result = self.service.uninstall()
            assert result is False  # Should return False on exception

    @patch("app.services.ufw.run")
    def test_ensure_ssh_allowed_add_ssh(self, mock_run):
        """Test _ensure_ssh_allowed adds SSH rule if it doesn't exist."""

        def side_effect(cmd, check=True, **kwargs):
            if cmd == ["ufw", "show", "added"]:
                result = Mock()
                result.stdout = "No rules found"  # No SSH rule
                result.returncode = 0
                return result
            elif cmd == ["ufw", "allow", "ssh"]:
                result = Mock()
                result.returncode = 0  # Success
                return result
            else:
                result = Mock()
                result.returncode = 0
                return result

        mock_run.side_effect = side_effect

        result = self.service._ensure_ssh_allowed()
        assert result is True
        # Should check for existing rules
        assert mock_run.called

    @patch("app.services.ufw.run")
    def test_ensure_ssh_allowed_add_ssh_fallback(self, mock_run):
        """Test _ensure_ssh_allowed falls back to numeric port if 'ssh' fails."""

        def side_effect(cmd, check=True, **kwargs):
            if cmd == ["ufw", "show", "added"]:
                result = Mock()
                result.stdout = "No rules found"
                result.returncode = 0
                return result
            elif cmd == ["ufw", "allow", "ssh"]:
                result = Mock()
                result.returncode = 1  # Failure
                return result
            elif cmd == ["ufw", "allow", "22"]:
                result = Mock()
                result.returncode = 0  # Success with numeric
                return result
            else:
                result = Mock()
                result.returncode = 0
                return result

        mock_run.side_effect = side_effect

        result = self.service._ensure_ssh_allowed()
        assert result is True
        # Should check for existing rules
        assert mock_run.called

    @patch("app.services.ufw.run")
    def test_ensure_ssh_allowed_returns_false_when_both_ssh_variants_fail(self, mock_run):
        def side_effect(cmd, check=True, **kwargs):
            if cmd == ["ufw", "show", "added"]:
                return Mock(returncode=0, stdout="No rules found")
            if cmd in (["ufw", "allow", "ssh"], ["ufw", "allow", "22"]):
                return Mock(returncode=1, stdout="")
            return Mock(returncode=0, stdout="")

        mock_run.side_effect = side_effect

        assert self.service._ensure_ssh_allowed() is False

    @patch("app.services.ufw.run")
    def test_get_status_returns_unknown_on_non_zero_exit(self, mock_run):
        mock_run.return_value = Mock(returncode=1, stdout="")
        status = self.service.get_status()
        assert "Статус установки: 🔴 не установлен" in status
        assert "Статус активации: 🔴 не активирован" in status
        assert "Вывод ufw status: недоступен" in status

    @patch("app.services.ufw.run")
    def test_enable_with_ssh_only_success(self, mock_run):
        """Test enabling UFW with SSH rule."""

        status_calls = 0

        def side_effect(cmd, check=True, **kwargs):
            nonlocal status_calls
            if isinstance(cmd, list) and len(cmd) >= 2 and cmd[0] == "ufw":
                if cmd[1] == "status":
                    result = Mock()
                    status_calls += 1
                    result.stdout = (
                        "Status: inactive\nSomething else\n"
                        if status_calls == 1
                        else "Status: active\nSomething else\n"
                    )
                    result.returncode = 0
                    return result
                elif cmd[1] == "--force" and cmd[2] == "enable":
                    result = Mock()
                    result.returncode = 0
                    return result
                elif cmd[0] == "ufw" and cmd[1] == "show":
                    result = Mock()
                    result.stdout = "22/tcp"
                    result.returncode = 0
                    return result
                elif cmd[0] == "ufw" and cmd[1] == "allow":
                    result = Mock()
                    result.returncode = 0
                    return result
                elif cmd[0] == "ufw" and cmd[1] == "default":
                    result = Mock()
                    result.returncode = 0
                    result.stdout = ""
                    return result
            elif isinstance(cmd, list) and cmd[0] == "which" and cmd[1] == "ufw":
                result = Mock()
                result.returncode = 0
                return result
            else:
                result = Mock()
                result.returncode = 0
                result.stdout = ""
                return result

        mock_run.side_effect = side_effect

        with patch.object(self.service, "is_installed", return_value=True):
            result = self.service.enable_with_ssh_only()
            assert result is True

    @patch("app.services.ufw.run")
    def test_enable_with_ssh_only_succeeds_when_enable_returns_nonzero_but_ufw_becomes_active(
        self, mock_run
    ):
        """Test enabling UFW tolerates false-negative return codes when final status is active."""

        status_calls = 0

        def side_effect(cmd, check=True, **kwargs):
            nonlocal status_calls
            if isinstance(cmd, list) and len(cmd) >= 2 and cmd[0] == "ufw":
                if cmd[1] == "status":
                    status_calls += 1
                    result = Mock()
                    result.stdout = (
                        "Status: inactive\n" if status_calls == 1 else "Status: active\n"
                    )
                    result.returncode = 0
                    return result
                elif cmd[1] == "--force" and cmd[2] == "enable":
                    result = Mock()
                    result.returncode = 1
                    result.stdout = ""
                    return result
                elif cmd[1] == "show":
                    result = Mock()
                    result.stdout = "22/tcp"
                    result.returncode = 0
                    return result
            elif isinstance(cmd, list) and cmd[0] == "which" and cmd[1] == "ufw":
                result = Mock()
                result.returncode = 0
                return result

            result = Mock()
            result.returncode = 0
            result.stdout = ""
            return result

        mock_run.side_effect = side_effect

        result = self.service.enable_with_ssh_only()

        assert result is True

    @patch("app.services.ufw.run")
    def test_enable_with_ssh_only_applies_safe_default_policies_before_enable(self, mock_run):
        """Test enabling UFW restores deny-incoming/allow-outgoing defaults before enable."""
        status_state = {"calls": 0}

        def side_effect(cmd, check=True, **kwargs):
            result = Mock()

            if cmd == ["which", "ufw"]:
                result.returncode = 0
            elif cmd == ["ufw", "status"]:
                status_state["calls"] += 1
                result.returncode = 0
                result.stdout = (
                    "Status: inactive\n" if status_state["calls"] == 1 else "Status: active\n"
                )
            elif cmd == ["ufw", "show", "added"]:
                result.returncode = 0
                result.stdout = "22/tcp\n"
            elif cmd == ["ufw", "default", "deny", "incoming"]:
                result.returncode = 0
                result.stdout = ""
            elif cmd == ["ufw", "default", "allow", "outgoing"]:
                result.returncode = 0
                result.stdout = ""
            elif cmd == ["ufw", "--force", "enable"]:
                result.returncode = 0
                result.stdout = ""
            else:
                result.returncode = 0
                result.stdout = ""

            return result

        mock_run.side_effect = side_effect

        result = self.service.enable_with_ssh_only()

        assert result is True
        assert ["ufw", "default", "deny", "incoming"] in [
            call.args[0] for call in mock_run.call_args_list
        ]
        assert ["ufw", "default", "allow", "outgoing"] in [
            call.args[0] for call in mock_run.call_args_list
        ]

    @patch("app.services.ufw.run")
    def test_enable_with_ssh_only_already_active(self, mock_run):
        """Test that enable_with_ssh_only returns True when UFW is already active."""

        def side_effect(cmd, check=True, **kwargs):
            if isinstance(cmd, list) and len(cmd) >= 2 and cmd[0] == "ufw":
                if cmd[1] == "status":
                    result = Mock()
                    result.stdout = "Status: active\n"
                    result.returncode = 0
                    return result
            # Return generic result for other commands
            result = Mock()
            result.returncode = 0
            result.stdout = ""
            return result

        mock_run.side_effect = side_effect

        # Mock is_installed to return True to skip installation step
        with patch.object(self.service, "is_installed", return_value=True):
            result = self.service.enable_with_ssh_only()
            assert result is True
            assert ["ufw", "default", "deny", "incoming"] in [
                call.args[0] for call in mock_run.call_args_list
            ]
            assert ["ufw", "default", "allow", "outgoing"] in [
                call.args[0] for call in mock_run.call_args_list
            ]

    @patch("app.services.ufw.run")
    def test_open_common_ports_success(self, mock_run):
        """Test opening common ports successfully."""

        def side_effect(cmd, check=True, **kwargs):
            result = Mock()
            result.returncode = 0
            result.stdout = ""
            return result

        mock_run.side_effect = side_effect

        result = self.service.open_common_ports()
        assert result is True
        # Should call allow for each port (80, 443, 25, 587, 993, 995) = 6 calls
        ufw_allow_calls = []
        for call in mock_run.call_args_list:
            cmd = call[0][0]  # The command being run
            if len(cmd) >= 2 and cmd[0] == "ufw" and cmd[1] == "allow":
                ufw_allow_calls.append(call)

        assert len(ufw_allow_calls) == 6  # 6 common ports

    @patch("app.services.ufw.run")
    def test_get_status_success(self, mock_run):
        """Test getting UFW status successfully."""
        expected_status = "Status: active\nsomething"
        mock_result = Mock()
        mock_result.stdout = expected_status
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = self.service.get_status()
        assert "Статус установки: 🟢 установлен" in result
        assert "Статус активации: 🟢 активирован" in result
        assert f"Вывод ufw status: {expected_status.strip()}" in result

    @patch("app.services.ufw.run")
    def test_disable_success(self, mock_run):
        """Test disabling UFW successfully."""

        def side_effect(cmd, check=True, **kwargs):
            if cmd == ["ufw", "status"]:
                result = Mock()
                result.stdout = "Status: active"
                result.returncode = 0
                return result
            elif (
                isinstance(cmd, list)
                and len(cmd) >= 2
                and cmd[0] == "bash"
                and "ufw disable" in cmd[1]
            ):
                result = Mock()
                result.returncode = 0
                return result
            else:
                result = Mock()
                result.returncode = 0
                result.stdout = ""
                return result

        mock_run.side_effect = side_effect

        result = self.service.disable()
        assert result is True

    @patch("app.services.ufw.run")
    def test_reset_success(self, mock_run):
        """Test resetting UFW successfully."""

        def side_effect(cmd, check=True, **kwargs):
            if (
                isinstance(cmd, list)
                and len(cmd) >= 2
                and cmd[0] == "bash"
                and "ufw reset" in cmd[1]
            ):
                result = Mock()
                result.returncode = 0
                return result
            else:
                result = Mock()
                result.returncode = 0
                result.stdout = ""
                return result

        mock_run.side_effect = side_effect

        result = self.service.reset()
        assert result is True

    @patch("app.services.ufw.run")
    def test_uninstall_success(self, mock_run):
        """Test uninstalling UFW successfully."""

        def side_effect(cmd, check=True, **kwargs):
            if cmd == ["which", "ufw"]:
                result = Mock()
                result.returncode = 0  # Installed
                return result
            elif cmd[0] == "apt" and cmd[1] == "remove":
                result = Mock()
                result.returncode = 0
                return result
            else:
                result = Mock()
                result.returncode = 0
                result.stdout = ""
                return result

        mock_run.side_effect = side_effect

        result = self.service.uninstall()
        assert result is True

    @patch("app.services.ufw.run")
    def test_open_port_success(self, mock_run):
        """Test opening a specific port successfully."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        result = self.service.open_port("80")
        assert result is True
        mock_run.assert_called_once_with(["ufw", "allow", "80"], check=False)

    @patch("app.services.ufw.run")
    def test_open_port_failure(self, mock_run):
        """Test opening a specific port fails."""
        mock_result = Mock()
        mock_result.returncode = 1  # Command failed
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        result = self.service.open_port("80")
        assert result is False

    @patch("app.services.ufw.run")
    def test_open_port_exception_handling(self, mock_run):
        """Test open_port handles exceptions properly."""

        def side_effect(cmd, check=True, **kwargs):
            raise RuntimeError("Test exception")

        mock_run.side_effect = side_effect

        result = self.service.open_port("80")
        assert result is False
