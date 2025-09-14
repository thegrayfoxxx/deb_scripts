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

    def uninstall_docker(self):
        run_commands(
            [
                [
                    "apt",
                    "purge",
                    "docker-ce",
                    "docker-ce-cli",
                    "containerd.io",
                    "docker-buildx-plugin",
                    "docker-compose-plugin",
                    "docker-ce-rootless-extras",
                ],
                ["rm", "-rf", "/var/lib/docker"],
                ["rm", "-rf", "/var/lib/containerd"],
                ["rm", "/etc/apt/sources.list.d/docker.list"],
                ["rm", "/etc/apt/keyrings/docker.asc"],
            ]
        )

    def interactive_run(self):
        print("Docker interactive")
        user_input = str(input("Exit - 0\nInstall - 1\nUninstall - 2\n"))
        match user_input:
            case "0":
                from scripts.run import run_interactive_script

                run_interactive_script()
            case "1":
                self.install_docker()
            case "2":
                self.uninstall_docker()
            case _:
                print("Invalid input")
                self.interactive_run()


if __name__ == "__main__":
    docker = Docker()
    docker.interactive_run()
