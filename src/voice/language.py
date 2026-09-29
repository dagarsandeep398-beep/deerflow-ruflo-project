"""Hindi-aware language helpers for the trading dialog.

Supports English and Hindi commands. Default language is Hindi.
"""

DEFAULT_LANGUAGE = 'hi'


def normalize_language(raw: str | None) -> str:
    if raw is None:
        return DEFAULT_LANGUAGE
    r = raw.strip().lower()
    if r in ('hi', 'hindi', 'hin'):
        return 'hi'
    if r in ('en', 'english', 'eng'):
        return 'en'
    return DEFAULT_LANGUAGE


def choose_text(lang: str, key: str, **kwargs) -> str:
    from src.voice.i18n import PROMPTS
    text = PROMPTS.get(lang, PROMPTS[DEFAULT_LANGUAGE]).get(key, key)
    return text.format(**kwargs) if kwargs else text
