from app.services.uv import UVService


def interactive_run():
    print("UV\nВыберите действие:")
    user_input = str(input("Выход - 0\nУстановить - 1\nУдалить - 2\n"))
    app = UVService()
    match user_input:
        case "0":
            from app.run import run_interactive_script

            run_interactive_script()
        case "1":
            app.install_uv()
        case "2":
            app.uninstall_uv()
        case _:
            print("Неверный ввод")
            interactive_run()
