from app.services.fail2ban import Fail2BanService


def interactive_run():
    print("Fail2Ban\nВыберете действие:")
    user_input = str(input("Установить - 1\nУдалить - 2\nВыход - 0\n"))
    fail2ban = Fail2BanService()
    match user_input:
        case "0":
            from app.interfaces.interactive.run import run_interactive_script

            run_interactive_script()
        case "1":
            fail2ban.install_fail2ban()
            interactive_run()
        case "2":
            fail2ban.uninstall_fail2ban()
            interactive_run()
        case _:
            print("Неверный ввод")
            interactive_run()
