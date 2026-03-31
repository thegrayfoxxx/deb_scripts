from contextvars import ContextVar
from typing import Final

from app.i18n.messages import EN_MESSAGES, RU_MESSAGES

DEFAULT_LOCALE: Final[str] = "ru"
SUPPORTED_LOCALES: Final[tuple[str, ...]] = ("ru", "en")

_current_locale: ContextVar[str] = ContextVar("current_locale", default=DEFAULT_LOCALE)

_MESSAGE_CATALOGS = {
    "ru": RU_MESSAGES,
    "en": EN_MESSAGES,
}


def get_locale() -> str:
    return _current_locale.get()


def set_locale(locale: str) -> None:
    normalized = locale.lower()
    if normalized not in SUPPORTED_LOCALES:
        msg = f"Unsupported locale: {locale}"
        raise ValueError(msg)
    _current_locale.set(normalized)


def translate(key: str, *, locale: str | None = None, **kwargs: object) -> str:
    resolved_locale = (locale or get_locale()).lower()
    catalog = _MESSAGE_CATALOGS.get(resolved_locale, RU_MESSAGES)
    template = catalog.get(key, RU_MESSAGES.get(key, key))
    return template.format(**kwargs)


def t(key: str, **kwargs: object) -> str:
    locale = kwargs.pop("locale", None)
    if locale is not None and not isinstance(locale, str):
        msg = "locale must be a string when provided"
        raise TypeError(msg)
    return translate(key, locale=locale, **kwargs)


def is_affirmative_reply(reply: str) -> bool:
    return reply.strip().lower() in {"y", "yes", "д", "да"}


def tr(ru: str, en: str) -> str:
    return ru if get_locale() == "ru" else en
