from unittest.mock import patch

import pytest

from app.bootstrap import args


class TestArgsUtils:
    def test_parse_args_uses_defaults(self):
        parsed = args.parse_args([])

        assert parsed.lang == "ru"
        assert parsed.log_level == "info"
        assert parsed.install is None
        assert parsed.uninstall is None
        assert parsed.activate is None
        assert parsed.deactivate is None
        assert parsed.status is None
        assert parsed.info is None
        assert parsed.all is False

    def test_parse_args_accepts_log_level_and_install_codes(self):
        parsed = args.parse_args(["--log-level", "debug", "--install", "1", "6"])

        assert parsed.lang == "ru"
        assert parsed.log_level == "debug"
        assert parsed.install == ["1", "6"]
        assert parsed.uninstall is None

    def test_parse_args_accepts_uninstall_codes(self):
        parsed = args.parse_args(["--uninstall", "2", "5"])

        assert parsed.log_level == "info"
        assert parsed.install is None
        assert parsed.uninstall == ["2", "5"]

    def test_parse_args_accepts_activate_deactivate_status_and_info_codes(self):
        parsed = args.parse_args(
            [
                "--activate",
                "1",
                "2",
                "--deactivate",
                "4",
                "--status",
                "3",
                "6",
                "--info",
                "5",
            ]
        )

        assert parsed.activate == ["1", "2"]
        assert parsed.deactivate == ["4"]
        assert parsed.status == ["3", "6"]
        assert parsed.info == ["5"]
        assert parsed.all is False

    def test_parse_args_accepts_all_flag_for_non_interactive_mode(self):
        parsed = args.parse_args(["--status", "--all"])

        assert parsed.status == []
        assert parsed.all is True

    def test_parse_args_rejects_empty_non_interactive_operation_without_all(self):
        with pytest.raises(SystemExit) as exc:
            args.parse_args(["--status"])

        assert exc.value.code == 2

    def test_parse_args_rejects_codes_together_with_all(self):
        with pytest.raises(SystemExit) as exc:
            args.parse_args(["--status", "1", "--all"])

        assert exc.value.code == 2

    def test_parse_args_rejects_invalid_log_level(self):
        with patch("sys.argv", ["script_name", "--log-level", "broken"]):
            try:
                args.parse_args(["--log-level", "broken"])
            except SystemExit as exc:
                assert exc.code == 2
            else:
                raise AssertionError("parse_args() should exit on invalid mode")

    def test_parse_args_help_includes_registry_service_codes(self, capsys):
        with pytest.raises(SystemExit) as exc:
            args.parse_args(["--help"])

        assert exc.value.code == 0
        help_output = capsys.readouterr().out
        assert "1=UFW" in help_output
        assert "6=UV" in help_output
        assert "--activate" in help_output
        assert "--deactivate" in help_output
        assert "--status" in help_output
        assert "--info" in help_output
        assert "--all" in help_output
        assert "--lang" in help_output

    def test_parse_args_help_switches_to_english(self, capsys):
        with pytest.raises(SystemExit) as exc:
            args.parse_args(["--lang", "en", "--help"])

        assert exc.value.code == 0
        help_output = capsys.readouterr().out
        assert "Console log level" in help_output
        assert "Interface language" in help_output
