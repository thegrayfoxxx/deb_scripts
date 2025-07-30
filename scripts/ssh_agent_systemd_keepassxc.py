import os
import subprocess
import configparser
from pathlib import Path

class SystemdManager:
    def __init__(self):
        self.user_dir = Path.home() / ".config/systemd/user"
        self.socket_content = """[Unit]
Description=SSH Agent Socket

[Socket]
ListenStream=%t/ssh-agent.socket
SocketMode=0600
Service=ssh-agent.service

[Install]
WantedBy=sockets.target
"""

        self.service_content = """[Unit]
Description=SSH Agent
Requires=ssh-agent.socket

[Service]
Type=simple
Restart=on-failure
RestartSec=5
Environment=SSH_AUTH_SOCK=%t/ssh-agent.socket
ExecStart=/usr/bin/ssh-agent -D -a ${SSH_AUTH_SOCK}

[Install]
WantedBy=default.target
"""

    def setup_systemd_services(self):
        try:
            self.user_dir.mkdir(parents=True, exist_ok=True)

            (self.user_dir / "ssh-agent.socket").write_text(self.socket_content)
            (self.user_dir / "ssh-agent.service").write_text(self.service_content)

            subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
            subprocess.run(["systemctl", "--user", "enable", "--now", "ssh-agent.socket"], check=True)
            subprocess.run(["systemctl", "--user", "enable", "--now", "ssh-agent.service"], check=True)

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Systemd error: {e}") from e

class KeePassXCConfigurator:
    def __init__(self):
        self.config_path = Path.home() / ".config/keepassxc/keepassxc.ini"
        self.ssh_agent_section = "SSHAgent"

    def configure_ssh_agent(self, socket_path):
        config = configparser.ConfigParser()
        config.read(self.config_path)

        if not config.has_section(self.ssh_agent_section):
            config.add_section(self.ssh_agent_section)

        config.set(self.ssh_agent_section, "Enabled", "true")
        config.set(self.ssh_agent_section, "AuthSockOverride", "true")
        config.set(self.ssh_agent_section, "AuthSockPath", socket_path)

        with open(self.config_path, "w") as config_file:
            config.write(config_file)

class EnvironmentConfigurator:
    def __init__(self):
        self.shell_rc = self._detect_shell_config()

    def _detect_shell_config(self):
        shell = os.environ.get("SHELL", "")
        if "zsh" in shell:
            return Path.home() / ".zshrc"
        return Path.home() / ".bashrc"

    def set_ssh_auth_sock(self, socket_path):
        export_line = f'export SSH_AUTH_SOCK="{socket_path}"\n'

        content = self.shell_rc.read_text() if self.shell_rc.exists() else ""
        if export_line not in content:
            with open(self.shell_rc, "a") as f:
                f.write(f"\n{export_line}")

class SSHSetupValidator:
    @staticmethod
    def verify_socket(socket_path):
        sp = Path(socket_path)
        return sp.exists() and sp.is_socket() and oct(sp.stat().st_mode)[-3:] == "600"

    @staticmethod
    def verify_ssh_agent():
        result = subprocess.run(["ssh-add", "-L"], capture_output=True, text=True)
        return result.returncode == 0 and "no identities" not in result.stdout.lower()

class SSHAgentSetup:
    def __init__(self):
        self.socket_path = f"{os.environ.get('XDG_RUNTIME_DIR', '/run/user/1000')}/ssh-agent.socket"

        self.systemd = SystemdManager()
        self.keepass = KeePassXCConfigurator()
        self.env = EnvironmentConfigurator()
        self.validator = SSHSetupValidator()

    def execute(self):
        print("Setting up systemd services...")
        self.systemd.setup_systemd_services()

        print("\nConfiguring environment...")
        self.env.set_ssh_auth_sock(self.socket_path)

        print("\nConfiguring KeePassXC...")
        self.keepass.configure_ssh_agent(self.socket_path)

        print("\nRunning final checks:")
        if not self.validator.verify_socket(self.socket_path):
            raise RuntimeError("Socket verification failed")

        if not self.validator.verify_ssh_agent():
            raise RuntimeError("SSH Agent verification failed")

        print("\nSuccess! Configuration completed.")
        print(f"1. Restart your terminal or run: source {self.env.shell_rc}")
        print("2. Open KeePassXC and unlock your database")
        print("3. Verify connection: ssh -T git@github.com")

if __name__ == "__main__":
    try:
        SSHAgentSetup().execute()
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("Please check:")
        print("- Systemd services status: systemctl --user status ssh-agent")
        print("- Socket permissions: ls -l $SSH_AUTH_SOCK")
        print("- KeePassXC SSH Agent settings")
        exit(1)
