import subprocess
import time

subprocess.run(["apt", "update"])
subprocess.run(["apt", "install", "fail2ban", "-y"])

path_to_jail_config = "/etc/fail2ban/jail.d/sshd.local"

jail_config = """
[sshd]
enabled = true
backend = systemd
journalmatch = _SYSTEMD_UNIT=ssh.service
maxretry = 5
port = ssh
bantime = 1d
findtime = 1h
"""

with open(path_to_jail_config, "w") as f:
    f.write(jail_config)

subprocess.run(["systemctl", "enable", "fail2ban"])
subprocess.run(["systemctl", "restart", "fail2ban"])
time.sleep(1)
subprocess.run(["systemctl", "status", "fail2ban"])
subprocess.run(["fail2ban-client", "status", "sshd"])
