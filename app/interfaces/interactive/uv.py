from app.services.uv import UVService


def interactive_run():
    print("UV\nВыберите действие:")
    user_input = str(input("Установить - 1\nУдалить - 2\nВыход - 0\n"))
    app = UVService()
    match user_input:
        case "0":
            from app.interfaces.interactive.run import run_interactive_script

            run_interactive_script()
        case "1":
            app.install_uv()
            interactive_run()
        case "2":
            app.uninstall_uv()
            interactive_run()
        case _:
            print("Неверный ввод")
            interactive_run()
