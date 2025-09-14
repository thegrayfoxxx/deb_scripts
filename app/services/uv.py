from pathlib import Path
from subprocess import run

from app.utils.subprocess_utils import run_commands


class UVService:
    home_path = Path.home()

    def install_uv(self):
        run_commands(
            [
                ["apt", "update"],
                ["apt", "install", "-y", "curl"],
                ["curl", "-LsSf", "https://astral.sh/uv/install.sh", "-o", "uv_install.sh"],
                ["sh", "./uv_install.sh"],
                ["bash", "-c", f'source "{self.home_path}/.local/bin/env"'],
                ["rm", "./uv_install.sh"],
            ]
        )

    def uninstall_uv(self):
        python_dir = run(["uv", "python", "dir"], capture_output=True, text=True).stdout.strip()
        tool_dir = run(["uv", "tool", "dir"], capture_output=True, text=True).stdout.strip()

        run_commands(
            [
                ["uv", "cache", "clean"],
                ["rm", "-r", python_dir],
                ["rm", "-r", tool_dir],
                ["rm", f"{self.home_path}/.local/bin/uv", f"{self.home_path}/.local/bin/uvx"],
            ]
        )
