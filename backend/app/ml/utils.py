import re
from razdel import tokenize
from pymorphy3 import MorphAnalyzer
from nltk.corpus import stopwords

# базовые стоп-слова + твои дополнительные
ru_stop = set(stopwords.words('russian')) | {
    "это", "так", "ещё", "еще", "просто", "очень", "свой",
    "который", "которые", "которое"
}

morph = MorphAnalyzer()

# регулярки
RE_URL  = re.compile(r"http\S+|www\.\S+", flags=re.IGNORECASE)
RE_MAIL = re.compile(r"\S+@\S+\.\S+")
RE_KEEP = re.compile(r"[a-zA-Zа-яА-Я0-9]+")

def normalize_basic(text: str) -> str:
    """Простая нормализация текста: убираем мусор, приводим к нижнему регистру"""
    if not isinstance(text, str):
        return ""
    t = text.replace("\xa0", " ").replace("\u200b", " ")
    t = RE_URL.sub(" ", t)
    t = RE_MAIL.sub(" ", t)
    t = t.replace("—", " ").replace("–", " ").replace("-", " ")
    t = re.sub(r"[^a-zA-Zа-яА-Я0-9 ]", " ", t)
    t = re.sub(r"\s+", " ", t).strip().lower()
    return t

def tokenize_lemma(text: str):
    """
    Токенизация для TF-IDF:
    - нормализация
    - razdel токенизация
    - фильтрация
    - лемматизация pymorphy3
    - удаление стоп-слов
    """
    t = normalize_basic(text)
    out = []
    for tok in tokenize(t):
        w = tok.text
        if not RE_KEEP.fullmatch(w):
            continue
        if w.isdigit():
            out.append(w)
            continue
        lemma = morph.normal_forms(w)[0]
        if lemma in ru_stop:
            continue
        out.append(lemma)
    return out
