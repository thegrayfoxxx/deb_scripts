from app.interfaces.interactive import bbr, docker, fail2ban, uv


def run_interactive_script():
    print("Добро пожаловать в deb_scripts!\nВыберите скрипт:")
    user_input = str(input("Выход - 0\nBBR - 1\nDocker - 2\nFail2Ban - 3\nUV - 4\n"))
    match user_input:
        case "0":
            exit()
        case "1":
            bbr.interactive_run()
        case "2":
            docker.interactive_run()
        case "3":
            fail2ban.interactive_run()
        case "4":
            uv.interactive_run()
        case _:
            print("Неверный ввод")
            run_interactive_script()
