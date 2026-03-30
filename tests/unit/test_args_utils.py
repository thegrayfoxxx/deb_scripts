from unittest.mock import patch

from app.utils import args_utils


class TestArgsUtils:
    def test_parse_args_uses_defaults(self):
        with patch("sys.argv", ["script_name"]):
            parsed = args_utils.parse_args()

        assert parsed.mode == "prod"
        assert parsed.install is None
        assert parsed.uninstall is None

    def test_parse_args_accepts_dev_mode_and_install_codes(self):
        with patch("sys.argv", ["script_name", "--mode", "dev", "--install", "1", "6"]):
            parsed = args_utils.parse_args()

        assert parsed.mode == "dev"
        assert parsed.install == ["1", "6"]
        assert parsed.uninstall is None

    def test_parse_args_accepts_uninstall_codes(self):
        with patch("sys.argv", ["script_name", "--uninstall", "2", "5"]):
            parsed = args_utils.parse_args()

        assert parsed.mode == "prod"
        assert parsed.install is None
        assert parsed.uninstall == ["2", "5"]

    def test_parse_args_rejects_invalid_mode(self):
        with patch("sys.argv", ["script_name", "--mode", "broken"]):
            try:
                args_utils.parse_args()
            except SystemExit as exc:
                assert exc.code == 2
            else:
                raise AssertionError("parse_args() should exit on invalid mode")

    def test_get_app_args_in_pytest_context_has_expected_defaults(self):
        args = args_utils.get_app_args()
        assert args.mode == "prod"
        assert args.install is None
        assert args.uninstall is None
