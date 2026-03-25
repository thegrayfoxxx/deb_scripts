from app.services.fail2ban import Fail2BanService


def display_fail2ban_submenu():
    """Отображает подменю для Fail2Ban с выбором действий"""
    print("\nДоступные действия для Fail2Ban:")
    user_input = str(
        input(
            "1 - 🔒 Установить Fail2Ban\n"
            "2 - 🔓 Удалить Fail2Ban\n"
            "00 - ℹ️ Информация о Fail2Ban\n"
            "0 - 🏠 Вернуться в главное меню\n"
            "Введите номер: "
        )
    )
    return user_input


def display_fail2ban_info():
    """Отображает информацию о Fail2Ban сервисе"""
    print("\n🛡️ Fail2Ban Intrusion Prevention Software")
    print("Fail2Ban — система автоматической защиты от атак подбора паролей и брутфорса")
    print("Основные возможности:")
    print("• Мониторинг логов систем и приложений")
    print("• Автоматическая блокировка подозрительных IP-адресов")
    print("• Защита от DDoS-атак и сканирования портов")
    print("• Настраиваемые правила фильтрации")
    print("• Поддержка различных сервисов (SSH, FTP, HTTP и др.)")
    print("• Логирование всех действий безопасности")
    print("🔗 GitHub репозиторий: https://github.com/fail2ban/fail2ban")
    print("\nДля возврата в меню нажмите любую клавишу")
    input()


def interactive_run():
    fail2ban = Fail2BanService()

    print("\n🛡️ Fail2Ban Intrusion Prevention Software")

    user_input = display_fail2ban_submenu()

    match user_input:
        case "0":
            from app.interfaces.interactive.run import run_interactive_script

            run_interactive_script()
        case "00":
            display_fail2ban_info()
            interactive_run()
        case "1":
            print("\nУстановка Fail2Ban...")
            fail2ban.install_fail2ban()
            print("\nFail2Ban успешно установлен!")
            interactive_run()
        case "2":
            print("\nУдаление Fail2Ban...")
            fail2ban.uninstall_fail2ban()
            print("\nFail2Ban успешно удален!")
            interactive_run()
        case _:
            print("Неверный ввод, попробуйте снова")
            interactive_run()
