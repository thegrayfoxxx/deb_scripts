import subprocess as sub
import time

from utils.subprocess_utils import run_commands


class Fail2Ban:
    def __init__(self):
        self.path_to_jail_config = "/etc/fail2ban/jail.d/sshd.local"
        self.jail_str_config = """
[sshd]
enabled = true
backend = systemd
journalmatch = _SYSTEMD_UNIT=ssh.service
maxretry = 5
port = ssh
bantime = 1d
findtime = 1h
"""

    def install_fail2ban(self):
        run_commands([["apt", "install", "fail2ban", "-y"]])

        with open(self.path_to_jail_config, "w") as f:
            f.write(self.jail_str_config)

        run_commands(
            [
                ["systemctl", "enable", "fail2ban"],
                ["systemctl", "restart", "fail2ban"],
            ]
        )

        status_service = ""
        while status_service != "active":
            status_service = sub.run(
                ["systemctl", "is-active", "fail2ban"], text=True, capture_output=True
            ).stdout.strip()
            time.sleep(0.5)

        run_commands(
            [
                ["systemctl", "status", "fail2ban"],
                ["fail2ban-client", "status", "sshd"],
            ]
        )

    def uninstall_fail2ban(self):
        run_commands(
            [
                ["systemctl", "disable", "fail2ban"],
                ["systemctl", "stop", "fail2ban"],
            ]
        )

        status_service = ""
        while status_service != "inactive":
            status_service = sub.run(
                ["systemctl", "is-active", "fail2ban"], text=True, capture_output=True
            ).stdout.strip()
            time.sleep(0.5)

        run_commands(
            [
                ["systemctl", "status", "fail2ban"],
                ["fail2ban-client", "status", "sshd"],
                ["apt", "remove", "fail2ban", "-y"],
                ["rm", "-f", self.path_to_jail_config],
            ]
        )

    def interactive_run(self):
        print("Fail2Ban install")
        user_input = str(input("Exit - 0\nInstall - 1\nUninstall - 2\n"))
        match user_input:
            case "0":
                exit(0)
            case "1":
                self.install_fail2ban()
            case "2":
                self.uninstall_fail2ban()
            case _:
                print("Invalid input")


if __name__ == "__main__":
    installer = Fail2Ban()
    installer.interactive_run()
