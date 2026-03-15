from app.services.bbr import BBRService


def interactive_run():
    print("BBR\nВыберите действие:")
    user_input = str(input("Включить - 1\nВыключить - 2\nВыход - 0\n"))
    bbr = BBRService()
    match user_input:
        case "0":
            from app.interfaces.interactive.run import run_interactive_script

            run_interactive_script()
        case "1":
            bbr.enable_bbr()
            interactive_run()
        case "2":
            bbr.disable_bbr()
            interactive_run()
        case _:
            print("Неверный ввод")
            interactive_run()
