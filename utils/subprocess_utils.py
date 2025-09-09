import subprocess as sub


def run_commands(commands: list[list[str]]) -> None:
    for command in commands:
        sub.run(command)
