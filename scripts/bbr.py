import time

from utils.subprocess_utils import run_commands


class BBR:
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

    def interactive_run(self):
        print("BBR interactive")
        user_input = str(input("Exit - 0\nEnable - 1\nDisable - 2\n"))
        bbr = BBR()
        match user_input:
            case "0":
                from scripts.run import run_interactive_script

                run_interactive_script()
            case "1":
                bbr.enable_bbr()
            case "2":
                bbr.disable_bbr()
            case _:
                print("Invalid input")


if __name__ == "__main__":
    installer = BBR()
    installer.interactive_run()
