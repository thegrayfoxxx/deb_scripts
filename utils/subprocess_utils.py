from subprocess import run


def run_commands(commands: list[list[str]]) -> None:
    for command in commands:
        run(command)
