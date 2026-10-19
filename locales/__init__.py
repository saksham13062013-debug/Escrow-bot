from .en import TEXTS as EN
from .hi import TEXTS as HI

LANGS = {
    "en": EN,
    "hi": HI,
}

def t(key: str, lang: str = "en", **kwargs) -> str:
    texts = LANGS.get(lang, EN)
    text = texts.get(key, EN.get(key, key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text
