import time

from app.utils.subprocess_utils import run_commands


class BBRService:
    def __init__(self):
        self.path_to_sysctl_config = "/etc/sysctl.conf"
        self.bbr_config = """
net.core.default_qdisc=fq_codel
net.ipv4.tcp_congestion_control=bbr
"""

    def enable_bbr(self):
        with open(self.path_to_sysctl_config, "a") as f:
            f.write(self.bbr_config)

        run_commands([["sysctl", "-p"]])
        time.sleep(1)
        run_commands(
            [["sysctl", "net.ipv4.tcp_congestion_control"], ["sysctl", "net.core.default_qdisc"]]
        )

    def disable_bbr(self):
        with open(self.path_to_sysctl_config, "r") as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith("net.ipv4.tcp_congestion_control") or line.startswith(
                    "net.core.default_qdisc"
                ):
                    lines.remove(line)
            with open(self.path_to_sysctl_config, "w") as f:
                f.writelines(lines)

        run_commands(
            [
                ["sysctl", "net.ipv4.tcp_congestion_control=cubic"],
                ["sysctl", "net.core.default_qdisc=fq_codel"],
                ["sysctl", "net.ipv4.tcp_congestion_control"],
                ["sysctl", "net.core.default_qdisc"],
            ]
        )
