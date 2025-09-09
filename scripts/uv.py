from utils.subprocess_utils import run_commands


class UV:
    def install_uv(self):
        commands = [
            ["apt", "update"],
            ["apt", "install", "-y", "curl"],
            ["curl", "-LsSf", "https://astral.sh/uv/install.sh", "-o", "uv_install.sh"],
            ["sh", "./uv_install.sh"],
            ["bash", "-c", 'source "$HOME/.local/bin/env"'],
            ["rm", "./uv_install.sh"],
        ]
        run_commands(commands)

    def interactive_run(self):
        print("UV install")
        user_input = str(input("Exit - 0\nInstall - 1\n"))
        match user_input:
            case "0":
                print("Exiting...")
            case "1":
                self.install_uv()
            case _:
                print("Invalid input")
                self.interactive_run()


if __name__ == "__main__":
    uv = UV()
    uv.interactive_run()
