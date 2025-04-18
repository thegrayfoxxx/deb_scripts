import os

os.system("apt update")
os.system("apt install fail2ban")

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

os.system("systemctl enable fail2ban")
os.system("systemctl restart fail2ban")
os.system("fail2ban-client status sshd")
