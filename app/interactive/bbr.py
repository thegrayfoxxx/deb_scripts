from app.services.bbr import BBRService


def interactive_run():
    print("BBR\nВыберите действие:")
    user_input = str(input("Выход - 0\nВключить - 1\nВыключить - 2\n"))
    bbr = BBRService()
    match user_input:
        case "0":
            from app.run import run_interactive_script

            run_interactive_script()
        case "1":
            bbr.enable_bbr()
        case "2":
            bbr.disable_bbr()
        case _:
            print("Неверный ввод")
            interactive_run()
