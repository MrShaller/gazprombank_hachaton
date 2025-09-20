# src/clause/splitter.py
import re
from typing import List, Tuple

# Контрастивные / поворотные маркеры тона (учитываем регистр через IGNORECASE)
CONTRAST = r"\b(но|однако|хотя|зато|при этом|с другой стороны)\b"

# Подсказки придаточных для мягкого сплита по запятым
CLAUSE_HINTS = r"\b(что|если|когда|потому что|так как|чтобы|хотя|однако|но)\b"

# Аббревиатуры/сокращения, которые не должны резаться по точкам
ABBR_PATTERNS = [
    r"\bт\.\s?д\.", r"\bт\.\s?п\.", r"\bи\.\s?т\.\s?д\.", r"\bи\.\s?т\.\s?п\.",
    r"\bг\.", r"\bул\.", r"\bпр\.", r"\bстр\.", r"\bдолл?\.", r"\bруб\.", r"\bмлн\.", r"\bмлрд\."
]

# Плейсхолдеры
PH_ABBR = "__ABBR{}__"
PH_NUM = "__NUM{}__"
PH_NO  = "__NO{}__"

def _protect(text: str) -> Tuple[str, dict]:
    """
    Заменяет аббревиатуры, сложные числа/валюты и конструкции '№ 928*****'
    на плейсхолдеры, чтобы не порезать их при сплите. Возвращает (text, mapping).
    """
    mapping = {}

    # 1) Аббревиатуры
    idx = 0
    def repl_abbr(m):
        nonlocal idx
        key = PH_ABBR.format(idx)
        mapping[key] = m.group(0)
        idx += 1
        return key

    for pat in ABBR_PATTERNS:
        text = re.sub(pat, repl_abbr, text, flags=re.IGNORECASE)

    # 2) Номера вида "№ 928*****"
    def repl_no(m):
        nonlocal idx
        key = PH_NO.format(idx)
        mapping[key] = m.group(0)
        idx += 1
        return key
    text = re.sub(r"№\s?[A-Za-zА-Яа-я0-9*]+", repl_no, text)

    # 3) Числа/валюта: «46 197, 97₽», «1 385 937,3 руб.» и т.п.
    # Схлопываем пробел после запятой/точки, защищаем всю группу
    def normalize_money_nums(s: str) -> str:
        # убираем пробел после запятой/точки внутри числа: "46197, 97" -> "46197,97"
        s = re.sub(r"(\d)[\s\u00A0]*([.,])[\s\u00A0]*(\d)", r"\1\2\3", s)
        return s

    text = normalize_money_nums(text)

    # Защитим паттерны вида "числа (с пробелами) ,/ . дробь + валюта (₽|руб.|руб)"
    num_pat = re.compile(r"(\d{1,3}(?:[\s\u00A0]\d{3})*(?:[.,]\d+)?(?:\s?(?:₽|руб\.?|р\.?))?)", flags=re.IGNORECASE)
    def repl_num(m):
        val = m.group(1)
        # Отсеиваем одиночные числа из 1-2 цифр, чтобы не засорять
        if len(re.sub(r"\D", "", val)) <= 2:
            return val
        nonlocal idx
        key = PH_NUM.format(idx)
        mapping[key] = val
        idx += 1
        return key

    text = re.sub(num_pat, repl_num, text)

    return text, mapping

def _unprotect(text: str, mapping: dict) -> str:
    # Восстанавливаем плейсхолдеры в исходный вид
    if not mapping:
        return text
    # Повторяем, пока все ключи не заменены (на случай пересечений)
    for _ in range(len(mapping) + 1):
        for k, v in mapping.items():
            text = text.replace(k, v)
    return text

def _normalize(text: str) -> str:
    text = text.replace("\u00A0", " ")
    text = re.sub(r"[ ]{2,}", " ", text)
    text = re.sub(r"[.!?]{3,}", r"..", text)  # длинные последовательности пунктуации немного схлопываем
    return text.strip()

def _split_sentences(text: str) -> List[str]:
    # Сплит по финальной пунктуации, НО плейсхолдеры уже защищены
    parts = re.split(r"(?<=[.!?…])\s+|\n+", text)
    return [p.strip() for p in parts if p.strip()]

def _split_by_contrast(sentence: str) -> List[str]:
    parts = re.split(f"({CONTRAST})", sentence, flags=re.IGNORECASE)
    if len(parts) == 1:
        return [sentence]
    out, buf = [], ""
    for i, chunk in enumerate(parts):
        if i % 2 == 0:  # текст
            if chunk.strip():
                buf += (chunk if not buf else " " + chunk)
        else:           # сам маркер "но/однако/..."
            if buf.strip():
                out.append(buf.strip())
            buf = chunk  # начинаем новую клаузу с маркера (сохраняем его в правой части)
    if buf.strip():
        out.append(buf.strip())
    # минимум 3 слова
    return [c.strip(" ,;—-") for c in out if len(c.strip(" ,;—-").split()) >= 3]

def _split_by_commas(sentence: str) -> List[str]:
    # Не резать по запятым, если вокруг чисел/валюты/формул
    if re.search(r"\d[=+×*/-]\d", sentence):
        return [sentence.strip()]

    chunks = [c.strip() for c in sentence.split(",")]
    if len(chunks) == 1:
        return [sentence]

    out = []
    buf = chunks[0]
    for nxt in chunks[1:]:
        # защита: если в левой или правой части видим подсказки придаточности/контраста — это граница клаузы
        cond_hint = re.search(CLAUSE_HINTS, buf, flags=re.IGNORECASE) or re.search(CLAUSE_HINTS, nxt, flags=re.IGNORECASE)
        # защита: если рядом есть плейсхолдер числа/аббревиатуры — НЕ режем
        near_num = (PH_NUM in buf) or (PH_NUM in nxt)
        near_abbr = (PH_ABBR in buf) or (PH_ABBR in nxt)
        if cond_hint and not (near_num or near_abbr) and len(buf.split()) >= 3:
            out.append(buf.strip())
            buf = nxt
        else:
            buf = f"{buf}, {nxt}"

    if buf.strip():
        out.append(buf.strip())

    out = [c.strip(" ,;—-") for c in out if len(c.strip(" ,;—-").split()) >= 3]
    return out if out else [sentence.strip()]

def _post_merge_short(clauses: List[str]) -> List[str]:
    """
    Склеиваем слишком короткие куски (<=2 слова или только пунктуация)
    с левым/правым соседом, чтобы убрать 'Программе.', '.', '!' и т.п.
    """
    if not clauses:
        return clauses
    clean = []

    def too_short(c: str) -> bool:
        words = [w for w in re.findall(r"\w+", c, flags=re.UNICODE)]
        return len(words) <= 2

    i = 0
    while i < len(clauses):
        c = clauses[i].strip()
        if too_short(c) or re.fullmatch(r"[.!?]+", c):
            # Пытаемся слить с правым, иначе с левым
            merged = None
            if i + 1 < len(clauses):
                merged = (c + " " + clauses[i + 1]).strip()
                i += 2
                clean.append(merged)
                continue
            elif clean:
                clean[-1] = (clean[-1] + " " + c).strip()
                i += 1
                continue
            else:
                # одиночный коротыш — пропускаем
                i += 1
                continue
        # Нормальная клауза
        # Убираем служебное начало вроде "и", "а", "да и" если оно тянется из середины
        c = re.sub(r"^(и|а|да и)\s+", "", c, flags=re.IGNORECASE)
        clean.append(c)
        i += 1

    return [re.sub(r"\s+", " ", c).strip(" ,;—-") for c in clean if c.strip()]

def split_into_clauses(text: str) -> List[str]:
    text = _normalize(text)
    text, mapping = _protect(text)

    sents = _split_sentences(text)
    clauses: List[str] = []
    for s in sents:
        for c in _split_by_contrast(s):
            clauses.extend(_split_by_commas(c))

    # склейка коротышей
    clauses = _post_merge_short(clauses)

    # восстанавливаем плейсхолдеры
    clauses = [_unprotect(c, mapping) for c in clauses]

    # финальная чистка и удаление дублей подряд
    cleaned = []
    for c in clauses:
        c = re.sub(r"\s+", " ", c).strip(" ,;—-")
        if c and (not cleaned or cleaned[-1] != c):
            cleaned.append(c)
    return cleaned
