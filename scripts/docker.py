from utils.subprocess_utils import run_commands


class Docker:
    def install_docker(self):
        run_commands(
            [
                ["apt", "update"],
                ["apt", "install", "-y", "curl"],
                ["curl", "-fsSL", "https://get.docker.com", "-o", "get-docker.sh"],
                ["sh", "./get-docker.sh"],
                ["rm", "./get-docker.sh"],
            ]
        )

    def interactive_run(self):
        print("Docker install")
        user_input = str(input("Exit - 0\nInstall - 1\n"))
        match user_input:
            case "0":
                print("Exiting...")
            case "1":
                self.install_docker()
            case _:
                print("Invalid input")
                self.interactive_run()


if __name__ == "__main__":
    docker = Docker()
    docker.interactive_run()
