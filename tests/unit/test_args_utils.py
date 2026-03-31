from unittest.mock import patch

import pytest

from app.bootstrap import args


class TestArgsUtils:
    def test_parse_args_uses_defaults(self):
        parsed = args.parse_args([])

        assert parsed.log_level == "info"
        assert parsed.install is None
        assert parsed.uninstall is None

    def test_parse_args_accepts_log_level_and_install_codes(self):
        parsed = args.parse_args(["--log-level", "debug", "--install", "1", "6"])

        assert parsed.log_level == "debug"
        assert parsed.install == ["1", "6"]
        assert parsed.uninstall is None

    def test_parse_args_accepts_uninstall_codes(self):
        parsed = args.parse_args(["--uninstall", "2", "5"])

        assert parsed.log_level == "info"
        assert parsed.install is None
        assert parsed.uninstall == ["2", "5"]

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
