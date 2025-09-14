from app.services.fail2ban import Fail2BanService


def interactive_run():
    print("Fail2Ban\nВыберете действие:")
    user_input = str(input("Выход - 0\nУстановить - 1\nУдалить - 2\n"))
    fail2ban = Fail2BanService()
    match user_input:
        case "0":
            from app.run import run_interactive_script

            run_interactive_script()
        case "1":
            fail2ban.install_fail2ban()
        case "2":
            fail2ban.uninstall_fail2ban()
        case _:
            print("Неверный ввод")
            interactive_run()
