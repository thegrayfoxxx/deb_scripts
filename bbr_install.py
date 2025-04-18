import time
import subprocess

bbr_config = """
net.core.default_qdisc=fq
net.ipv4.tcp_congestion_control=bbr
"""

path = "/etc/sysctl.conf"


with open(path, "a") as f:
    f.write(bbr_config)

subprocess.run(["sysctl", "-p"])
time.sleep(1)
subprocess.run(["sysctl", "net.ipv4.tcp_congestion_control"])
