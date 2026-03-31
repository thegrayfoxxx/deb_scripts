from dataclasses import dataclass
from typing import Callable, Iterable, Sequence, TypeAlias

from app.core.status import status_badge
from app.i18n.locale import t

MenuAction: TypeAlias = Callable[[], object]


@dataclass(frozen=True)
class MenuItem:
    key: str
    label: str
    action: MenuAction
    status_renderer: Callable[[], str] | None = None


def format_menu_line(item: MenuItem) -> str:
    """Форматирует строку пункта меню с опциональным кратким статусом."""
    if item.status_renderer is None:
        return item.label
    return f"{item.label} ({item.status_renderer()})"


def prompt_menu(
    header: str,
    items: Sequence[MenuItem],
    info_label: str | None = None,
    exit_label: str | None = None,
) -> str:
    """Печатает меню и возвращает выбор пользователя."""
    print(f"\n{header}")
    resolved_info_label = info_label or t("menu.info_label")
    resolved_exit_label = exit_label or t("menu.back_label")
    prompt_lines = [format_menu_line(item) for item in items]
    prompt_lines.extend([resolved_info_label, resolved_exit_label, t("common.enter_number")])
    return str(input("\n".join(prompt_lines)))


def return_to_previous_menu(message: str | None = None) -> None:
    """Печатает сообщение о возврате и завершает текущий цикл меню."""
    print(message or t("menu.back_message"))


def return_to_main_menu() -> None:
    """Печатает стандартное сообщение о возврате в главное меню."""
    return_to_previous_menu(t("menu.service_exit_message"))


def prompt_service_submenu(
    *,
    header: str,
    items: Sequence[MenuItem],
    info_label: str,
) -> str:
    """Печатает стандартное сервисное подменю и возвращает выбор пользователя."""
    return prompt_menu(
        header=header,
        items=items,
        info_label=info_label,
        exit_label=t("menu.service_exit_label"),
    )


def build_standard_service_menu_items(
    *,
    service,
    primary_key: str,
    primary_label: str,
    primary_action: MenuAction,
    primary_is_ok: Callable[[], bool],
    primary_ok_text: str,
    primary_fail_text: str,
    uninstall_key: str,
    uninstall_label: str,
    uninstall_action: MenuAction,
    status_key: str,
    status_label: str,
) -> list[MenuItem]:
    """Строит типовое меню: основное действие, удаление и показ статуса."""

    def render_primary_status() -> str:
        is_ok = primary_is_ok()
        return status_badge(is_ok, primary_ok_text, primary_fail_text)

    return [
        MenuItem(
            key=primary_key,
            label=primary_label,
            action=primary_action,
            status_renderer=render_primary_status,
        ),
        MenuItem(key=uninstall_key, label=uninstall_label, action=uninstall_action),
        MenuItem(key=status_key, label=status_label, action=lambda: print(service.get_status())),
    ]


def show_info_screen(title: str, lines: Sequence[str]) -> None:
    """Печатает типовой информационный экран и ждёт подтверждения пользователя."""
    print(f"\n{title}")
    for line in lines:
        print(line)
    print(f"\n{t('common.press_any_key')}")
    input()


def run_menu_loop(
    *,
    title: str,
    header: str,
    items: Sequence[MenuItem] | None = None,
    items_factory: Callable[[], Sequence[MenuItem]] | None = None,
    info_handler: Callable[[], None],
    exit_handler: Callable[[], None],
    intro_lines: Iterable[str] = (),
    info_label: str | None = None,
    exit_label: str | None = None,
    invalid_message: str | None = None,
) -> None:
    """Универсальный цикл интерактивного меню."""
    if (items is None) == (items_factory is None):
        msg = t("menu.requires_items_or_factory")
        raise ValueError(msg)

    resolved_items_factory = items_factory

    while True:
        if items is not None:
            current_items = items
        else:
            assert resolved_items_factory is not None
            current_items = resolved_items_factory()
        actions = {item.key: item.action for item in current_items}

        print(f"\n{title}")
        for line in intro_lines:
            print(line)

        user_input = prompt_menu(
            header=header,
            items=current_items,
            info_label=info_label,
            exit_label=exit_label,
        )

        if user_input == "0":
            exit_handler()
            return

        if user_input == "00":
            info_handler()
            continue

        action = actions.get(user_input)
        if action is None:
            print(invalid_message or t("common.invalid_option"))
            continue

        action()
