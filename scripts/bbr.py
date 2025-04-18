import subprocess
import time


class BBR:
    def __init__(self):
        self.path_to_sysctl_config = "/etc/sysctl.conf"
        self.bbr_config = """
net.core.default_qdisc=fq_codel
net.ipv4.tcp_congestion_control=bbr
"""

    def install_bbr(self):
        with open(self.path_to_sysctl_config, "a") as f:
            f.write(self.bbr_config)

        subprocess.run(["sysctl", "-p"])
        time.sleep(1)
        subprocess.run(["sysctl", "net.ipv4.tcp_congestion_control"])
        subprocess.run(["sysctl", "net.core.default_qdisc"])

    def uninstall_bbr(self):
        with open(self.path_to_sysctl_config, "r") as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith(
                    "net.ipv4.tcp_congestion_control"
                ) or line.startswith("net.core.default_qdisc"):
                    lines.remove(line)
            with open(self.path_to_sysctl_config, "w") as f:
                f.writelines(lines)
        subprocess.run(["sysctl", "net.ipv4.tcp_congestion_control=cubic"])
        subprocess.run(["sysctl", "net.core.default_qdisc=fq_codel"])
        subprocess.run(["sysctl", "net.ipv4.tcp_congestion_control"])
        subprocess.run(["sysctl", "net.core.default_qdisc"])

if __name__ == "__main__":
    user_input = input("Exit - 0\nInstall - 1\nUninstall - 2\n")
    bbr = BBR()
    match user_input:
        case "0":
            exit(0)
        case "1":
            bbr.install_bbr()
        case "2":
            bbr.uninstall_bbr()
