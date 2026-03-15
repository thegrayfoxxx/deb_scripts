from app.services.traffic_guard import TrafficGuardService


def interactive_run():
    print("TrafficGuard\nВыберите действие:")
    user_input = str(input("Установить - 1\nУдалить - 2\nВыход - 0\n"))
    traffic_guard = TrafficGuardService()
    match user_input:
        case "0":
            from app.interfaces.interactive.run import run_interactive_script

            run_interactive_script()
        case "1":
            traffic_guard.install_trafficguard()
            interactive_run()
        case "2":
            traffic_guard.uninstall_trafficguard()
            interactive_run()
        case _:
            print("Неверный ввод")
            interactive_run()
