from app.services.docker import DockerService


def interactive_run():
    print("Docker\nВыберите действие:")
    user_input = str(input("Установить - 1\nУдалить - 2\nВыход - 0\n"))
    docker = DockerService()
    match user_input:
        case "0":
            from app.interfaces.interactive.run import run_interactive_script

            run_interactive_script()
        case "1":
            docker.install_docker()
            interactive_run()
        case "2":
            docker.uninstall_docker()
            interactive_run()
        case _:
            print("Неверный ввод")
            interactive_run()
