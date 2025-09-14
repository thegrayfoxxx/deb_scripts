from app.services.docker import DockerService


def interactive_run():
    print("Docker\nВыберите действие:")
    user_input = str(input("Выход - 0\nУстановить - 1\nУдалить - 2\n"))
    docker = DockerService()
    match user_input:
        case "0":
            from app.run import run_interactive_script

            run_interactive_script()
        case "1":
            docker.install_docker()
        case "2":
            docker.uninstall_docker()
        case _:
            print("Неверный ввод")
            interactive_run()
