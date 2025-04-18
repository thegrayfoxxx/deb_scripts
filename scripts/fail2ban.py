import subprocess
import time


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
        subprocess.run(["apt", "install", "fail2ban", "-y"])

        with open(self.path_to_jail_config, "w") as f:
            f.write(self.jail_str_config)

        subprocess.run(["systemctl", "enable", "fail2ban"])
        subprocess.run(["systemctl", "restart", "fail2ban"])
        time.sleep(1)
        subprocess.run(["systemctl", "status", "fail2ban"])
        subprocess.run(["fail2ban-client", "status", "sshd"])

    def uninstall_fail2ban(self):
        subprocess.run(["systemctl", "stop", "fail2ban"])
        subprocess.run(["systemctl", "disable", "fail2ban"])
        subprocess.run(["apt", "remove", "fail2ban", "-y"])
        subprocess.run(["rm", "-f", self.path_to_jail_config])

if __name__ == "__main__":
    user_input = input("exit - 0\ninstall - 1\nuninstall - 2\n")
    installer = Fail2Ban()
    if user_input == "0":
        exit(0)
    elif user_input == "1":
        installer.install_fail2ban()
    elif user_input == "2":
        installer.uninstall_fail2ban()
