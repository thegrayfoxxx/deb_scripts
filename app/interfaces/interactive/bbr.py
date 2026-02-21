from app.services.bbr import BBRService


def interactive_run():
    print("BBR\nВыберите действие:")
    user_input = str(input("Выход - 0\nВключить - 1\nВыключить - 2\n"))
    bbr = BBRService()
    match user_input:
        case "0":
            from app.interfaces.interactive.run import run_interactive_script

            run_interactive_script()
        case "1":
            result = bbr.enable_bbr()
            print(result[1])
        case "2":
            result = bbr.disable_bbr()
            print(result[1])
        case _:
            print("Неверный ввод")
            interactive_run()
