import subprocess


def run(command: list[str], check: bool = True, **kwargs) -> subprocess.CompletedProcess:
    """
    Запускает команду через subprocess.

    :param check: Если False — не выбрасывать исключение при ошибке
    """
    try:
        return subprocess.run(args=command, check=check, text=True, capture_output=True, **kwargs)
    except subprocess.CalledProcessError as e:
        if check:
            raise
        # Если check=False, возвращаем результат с ошибкой
        return e


def is_command_available(cmd: str) -> bool:
    """Проверяет, доступна ли команда в системе"""
    try:
        result = run([cmd, "--version"], check=False)
        return result.returncode == 0
    except FileNotFoundError:
        return False
