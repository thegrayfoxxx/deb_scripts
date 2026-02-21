import os
import subprocess
import time
from typing import List, Tuple

from app.utils.subprocess_utils import run_commands


class BBRService:
    def __init__(self):
        self.path_to_bbr_module_config = "/etc/modules-load.d/bbr.conf"
        self.path_to_bbr_sysctl_config = "/etc/sysctl.d/10-bbr-fq_codel.conf"
        self.cubic = "net.ipv4.tcp_congestion_control=cubic"
        self.bbr = "net.ipv4.tcp_congestion_control=bbr"
        self.fq_codel = "net.core.default_qdisc=fq_codel"
        self.safe_config = f"{self.cubic}\n{self.fq_codel}"
        self.bbr_config = f"{self.bbr}\n{self.fq_codel}"

    def _check_root(self):
        """Проверка прав суперпользователя"""
        if os.geteuid() != 0:
            raise PermissionError("Скрипт требует прав root (sudo)")

    def _is_module_loaded(self) -> bool:
        """Проверяет, загружен ли модуль ядра"""
        try:
            result = subprocess.run(["lsmod"], capture_output=True, text=True, check=True)
            return "tcp_bbr" in result.stdout
        except subprocess.CalledProcessError:
            return False

    def _run_sysctl(self, args: List[str]) -> bool:
        """Обертка для запуска sysctl с обработкой ошибок"""
        try:
            cmd = ["sysctl"] + args
            run_commands([cmd])
            return True
        except Exception as e:
            print(f"Ошибка sysctl {' '.join(cmd)}: {e}")  # type:ignore
            return False

    def enable_bbr(self) -> Tuple[bool, str]:
        """Включает BBR. Возвращает (успех, сообщение)"""
        try:
            self._check_root()

            if not self._is_module_loaded():
                print("Загрузка модуля tcp_bbr...")
                run_commands([["modprobe", "tcp_bbr"]])
                time.sleep(0.5)
                if not self._is_module_loaded():
                    return False, "Не удалось загрузить модуль tcp_bbr"

            with open(self.path_to_bbr_module_config, "w") as f:
                f.write("tcp_bbr\n")

            with open(self.path_to_bbr_sysctl_config, "w") as f:
                f.write(self.bbr_config)

            print("Применение настроек sysctl...")
            run_commands([["sysctl", "--system"]])

            result = subprocess.run(
                ["sysctl", "net.ipv4.tcp_congestion_control"], capture_output=True, text=True
            )
            if "bbr" in result.stdout:
                return True, "BBR успешно включен"
            else:
                return False, "Настройки не применились (проверьте вывод sysctl)"

        except Exception as e:
            return False, f"Ошибка: {str(e)}"

    def disable_bbr(self) -> Tuple[bool, str]:
        """Отключает BBR (возвращает cubic). Возвращает (успех, сообщение)"""
        try:
            self._check_root()

            with open(self.path_to_bbr_sysctl_config, "w") as f:
                f.write(self.safe_config)

            run_commands([["sysctl", "-w", "net.ipv4.tcp_congestion_control=cubic"]])
            run_commands([["sysctl", "-w", "net.core.default_qdisc=fq_codel"]])

            result = subprocess.run(
                ["sysctl", "net.ipv4.tcp_congestion_control"], capture_output=True, text=True
            )
            if "cubic" in result.stdout:
                return True, "BBR выключен (возвращен cubic)"
            else:
                return False, "Не удалось переключить на cubic"

        except Exception as e:
            return False, f"Ошибка: {str(e)}"
