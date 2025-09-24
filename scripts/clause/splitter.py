import os
import re
import yaml
import logging
from pathlib import Path
from functools import lru_cache
from typing import List, Tuple
# =========================
# Конфиги и константы
# =========================

DEFAULT_TOPICS_YAML = Path(__file__).resolve().parents[2] / "configs" / "topics.yml"

# Контрастивные / поворотные маркеры тона
CONTRAST = r"\b(но|однако|хотя|зато|при этом|с другой стороны)\b"

# Подсказки придаточных: где можно мягко резать по запятым
CLAUSE_HINTS = r"\b(что|если|когда|пока|потому что|так как|чтобы|хотя|однако|но|причём|причем|а)\b"

# Аббревиатуры/сокращения, которые не должны резаться по точкам
ABBR_PATTERNS = [
    r"\bт\.\s?к\.",  # т.к.
    r"\bт\.\s?д\.", r"\bт\.\s?п\.",  # т.д., т.п.
    r"\bи\.\s?т\.\s?д\.", r"\bи\.\s?т\.\s?п\.",  # и т.д., и т.п.
    r"\bг\.", r"\bул\.", r"\bпр\.", r"\bстр\.", r"\bдолл?\.", r"\bруб\.", r"\bмлн\.", r"\bмлрд\.",
    r"\bдоп\.",
    r"\b[А-Яа-яЁё]\.\s?[А-Яа-яЁё]\."  # «X. Y.»
]

# Вводные фразы, которые как отдельные клаузы малоинформативны
INTRO_PHRASES = re.compile(
    r"^(?:оказывается|к слову|кстати|на следующий день|мораль такова|в итоге|итак)\b",
    flags=re.IGNORECASE
)

# Плейсхолдеры
PH_ABBR = "__ABBR{}__"
PH_NUM  = "__NUM{}__"
PH_NO   = "__NO{}__"

# Стоп-слова и пороги
RU_STOP = set("""
и а но однако хотя зато при этом с другой стороны что чтобы как когда где куда откуда потому так как
да или либо то есть это тот та те о об от до из из-за за для при по на со соотв то есть т е и т д
""".split())

MIN_WORDS = 7
MIN_WORDS_COMMA = 6
MIN_WORDS_SHORT_GLUE = 5

CONNECTIVE_ONLY = re.compile(
    r"^(?:и|а|но|однако|хотя|зато|при этом|с другой стороны)\.?$",
    flags=re.IGNORECASE
)
DUP_CONNECTIVE = re.compile(
    r"\b(при этом|однако|но|хотя|зато|с другой стороны)\b(\s+\1\b)+",
    flags=re.IGNORECASE
)
SUBORD_START = re.compile(
    r"^(?:что|чтобы|чем|котор(?:ый|ая|ое|ые)|где|когда|куда|откуда|потому что|так как)\b",
    flags=re.IGNORECASE
)

# Базовые доменные ключи (в дополнение к topics.yml)
BASE_DOMAIN_KEYWORDS = [
    r"дебетов[а-я]*", r"кредитн[а-я]*", r"ипотек[а-я]*",
    r"автокредит", r"рефинансир[а-я]*",
    r"дистанционн[а-я]*", r"перевод[а-я]*", r"карта",
    r"оформит[а-я]*", r"одобрени[а-я]*", r"лимит",
    r"ставк[а-я]*", r"плат[её]ж", r"списани[ея]",
    r"комисс[а-я]*", r"кэшбэк",
    r"(?:руб\.?|₽|р\.?|тыс\.?|млн|млрд)"
]

# =========================
# Загрузка topic-синонимов и компиляция паттернов
# =========================

def _ensure_regex(s: str) -> str:
    return s

@lru_cache(maxsize=1)
def load_topic_synonyms(config_path: str | Path | None = None) -> dict:
    path = Path(config_path) if config_path else Path(
        os.getenv("CLAUSE_TOPICS_YAML", DEFAULT_TOPICS_YAML)
    )
    if not path.exists():
        logging.warning(f"[clause] topics.yml not found at {path}. Falling back to BASE_DOMAIN_KEYWORDS only.")
        return {}

    with path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    topics = {}
    if isinstance(cfg, dict) and "topics" in cfg:
        for t in cfg["topics"] or []:
            syns = t.get("synonyms") or []
            syns = [str(x) for x in syns if isinstance(x, (str, int, float))]
            topics[t.get("id") or "UNK"] = [_ensure_regex(s) for s in syns]
    else:
        logging.warning("[clause] topics.yml doesn't contain 'topics' list")
    return topics

@lru_cache(maxsize=1)
def compile_topic_patterns(config_path: str | Path | None = None) -> List[re.Pattern]:
    topics = load_topic_synonyms(config_path)
    pats: List[re.Pattern] = []
    for syns in topics.values():
        for s in syns:
            try:
                pats.append(re.compile(s, flags=re.IGNORECASE))
            except re.error as e:
                logging.warning(f"[clause] bad regex in topics.yml: {s!r} ({e})")
    for s in BASE_DOMAIN_KEYWORDS:
        pats.append(re.compile(s, flags=re.IGNORECASE))
    return pats

# Сначала собираем список паттернов...
DOMAIN_PATTERNS = compile_topic_patterns()

# ...затем схлопываем в один большой regex и кэшируем проверки
def _compile_big_domain_pattern() -> re.Pattern:
    pats = [p.pattern for p in DOMAIN_PATTERNS]
    if not pats:
        return re.compile(r"(?!x)")
    big = r"(?:" + r")|(?:".join(pats) + r")"
    return re.compile(big, flags=re.IGNORECASE)

BIG_DOMAIN_RE = _compile_big_domain_pattern()

@lru_cache(maxsize=50000)
def _has_domain_keyword(s: str) -> bool:
    return bool(BIG_DOMAIN_RE.search(s))

# =========================
# Нормализация и защита
# =========================

def _precanon_abbrs(text: str) -> str:
    pairs = [
        (r"[тТ]\s?\.\s?[кК]\s?\.", "т.к."),
        (r"[тТ]\s?\.\s?[дД]\s?\.", "т.д."),
        (r"[тТ]\s?\.\s?[пП]\s?\.", "т.п."),
        (r"[иИ]\s?\.\s?[тТ]\s?\.\s?[дД]\s?\.", "и т.д."),
        (r"[иИ]\s?\.\s?[тТ]\s?\.\s?[пП]\s?\.", "и т.п."),
        (r"[дД]\s?оп\s?\.", "доп.")
    ]
    for pat, rep in pairs:
        text = re.sub(pat, rep, text)
    return text

def _protect(text: str) -> Tuple[str, dict]:
    mapping = {}
    text = _precanon_abbrs(text)

    idx = 0
    def repl_abbr(m):
        nonlocal idx
        key = PH_ABBR.format(idx); mapping[key] = m.group(0); idx += 1; return key
    for pat in ABBR_PATTERNS:
        text = re.sub(pat, repl_abbr, text, flags=re.IGNORECASE)

    def repl_no(m):
        nonlocal idx
        key = PH_NO.format(idx); mapping[key] = m.group(0); idx += 1; return key
    text = re.sub(r"№\s?[A-Za-zА-Яа-я0-9*]+", repl_no, text)

    def normalize_money_nums(s: str) -> str:
        return re.sub(r"(\d)[\s\u00A0]*([.,])[\s\u00A0]*(\d)", r"\1\2\3", s)
    text = normalize_money_nums(text)

    num_pat = re.compile(r"(\d{1,3}(?:[\s\u00A0]\d{3})*(?:[.,]\d+)?(?:\s?(?:₽|руб\.?|р\.?))?)", flags=re.IGNORECASE)
    def repl_num(m):
        nonlocal idx
        val = m.group(1)
        if len(re.sub(r"\D", "", val)) <= 2:
            return val
        key = PH_NUM.format(idx); mapping[key] = val; idx += 1; return key
    text = re.sub(num_pat, repl_num, text)

    return text, mapping

def _unprotect(text: str, mapping: dict) -> str:
    if not mapping:
        return text
    for _ in range(len(mapping) + 1):
        for k, v in mapping.items():
            text = text.replace(k, v)
    return text

def _normalize(text: str) -> str:
    text = text.replace("\u00A0", " ")
    text = re.sub(r"[ ]{2,}", " ", text)
    text = re.sub(r"[.!?]{3,}", r"..", text)
    return text.strip()

# =========================
# Вспомогательные эвристики
# =========================

def _words_ru(s: str) -> List[str]:
    return re.findall(r"[A-Za-zА-Яа-яЁё]+", s, flags=re.UNICODE)

def _has_content_word(s: str) -> bool:
    ws = _words_ru(s.lower())
    for w in ws:
        if w in RU_STOP:
            continue
        if len(w) >= 4:
            return True
        if re.search(r"(ть|л|ла|ли|ло|ем|ете|ет|ют|ишь|ит|им|ите|у|ю)$", w):
            return True
    return False

def _looks_like_money_fragment(s: str) -> bool:
    return bool(re.search(r"\b(?:руб\.?|р\.?|₽|тыс\.?|млн|млрд)\b", s, flags=re.IGNORECASE))

def _looks_like_date(s: str) -> bool:
    return bool(re.search(r"\b\d{1,2}[.\-/]\d{1,2}([.\-/]\d{2,4})?\b", s))

def _mostly_digits_punct(s: str) -> bool:
    return len(re.sub(r"[0-9\s.,;:—\-()/+*%№*]", "", s)) == 0

def _ends_sentence(s: str) -> bool:
    return bool(re.search(r"[.!?…]\s*$", s))

def _is_parenthetical(c: str) -> bool:
    cs = c.strip()
    return cs.startswith("(") or cs.endswith(")")

def _is_money_short(c: str) -> bool:
    return _looks_like_money_fragment(c) and len(_words_ru(c)) <= 6

# =========================
# Сплиты
# =========================

def _split_sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[.!?…])\s+|(?<=[.!?…])(?=\S)|\n+", text)
    return [p.strip() for p in parts if p.strip()]

def _split_by_quotes(sentence: str) -> List[str]:
    parts = re.split(r'(".*?")', sentence)
    if len(parts) == 1:
        return [sentence]
    out, buf = [], ""
    for chunk in parts:
        if not chunk:
            continue
        if chunk.startswith('"') and chunk.endswith('"'):
            if buf.strip():
                out.append(buf.strip())
                buf = chunk
            else:
                buf = chunk
        else:
            buf = (f"{buf} {chunk}".strip() if buf else chunk.strip())
    if buf:
        out.append(buf.strip())
    final = []
    for p in out:
        final.extend(re.split(r'(?<=")\s+(?=[А-ЯA-Z])', p))
    return [x.strip() for x in final if x.strip()]

def _split_by_contrast(sentence: str) -> List[str]:
    parts = re.split(f"({CONTRAST})", sentence, flags=re.IGNORECASE)
    if len(parts) == 1:
        return [sentence]
    out, buf = [], ""
    for i, chunk in enumerate(parts):
        if i % 2 == 0:
            if chunk.strip():
                buf += (chunk if not buf else " " + chunk)
        else:
            if buf.strip():
                out.append(buf.strip())
            buf = chunk
    if buf.strip():
        out.append(buf.strip())
    return [c.strip(" ,;—-") for c in out if len(c.strip(" ,;—-").split()) >= 3]

def _split_long_by_and(sentence: str) -> List[str]:
    if len(_words_ru(sentence)) < 20:
        return [sentence]
    parts = re.split(r",\s+(?i:и)\s+", sentence)
    if len(parts) == 1:
        return [sentence]
    out, buf = [], parts[0]
    for nxt in parts[1:]:
        if len(_words_ru(buf)) >= MIN_WORDS_COMMA and len(_words_ru(nxt)) >= MIN_WORDS_COMMA:
            out.append(buf.strip()); buf = nxt
        else:
            buf = f"{buf}, и {nxt}"
    out.append(buf.strip())
    return out

def _split_by_commas(sentence: str) -> List[str]:
    if re.search(r"\d[=+×*/-]\d", sentence):
        return [sentence.strip()]

    chunks = [c.strip() for c in sentence.split(",")]
    if len(chunks) == 1:
        return [sentence.strip()]

    out = []
    buf = chunks[0]
    for nxt in chunks[1:]:
        cond_hint = re.search(CLAUSE_HINTS, buf, flags=re.IGNORECASE) or re.search(CLAUSE_HINTS, nxt, flags=re.IGNORECASE)
        near_num = (PH_NUM in buf) or (PH_NUM in nxt)
        near_abbr = (PH_ABBR in buf) or (PH_ABBR in nxt)

        buf_words = len(_words_ru(buf))
        nxt_words = len(_words_ru(nxt))

        min_words_comma = MIN_WORDS_COMMA
        if len(_words_ru(sentence)) >= 25:
            min_words_comma = max(4, MIN_WORDS_COMMA - 1)

        should_cut = (
            cond_hint
            and not (near_num or near_abbr)
            and buf_words >= min_words_comma
            and nxt_words >= min_words_comma
        )

        if should_cut:
            out.append(buf.strip()); buf = nxt
        else:
            buf = f"{buf}, {nxt}"

    if buf.strip():
        out.append(buf.strip())

    out = [c.strip(" ,;—-") for c in out if len(_words_ru(c)) >= MIN_WORDS]
    return out if out else [sentence.strip()]

# =========================
# Фильтры и склейки
# =========================

def _is_low_content_clause(s: str) -> bool:
    s = s.strip(" ,;—-")
    if not s:
        return True
    if _has_domain_keyword(s):
        return False
    if _mostly_digits_punct(s) or _looks_like_date(s) or _looks_like_money_fragment(s):
        return True
    words = _words_ru(s)
    if len(words) < MIN_WORDS and not _has_content_word(s):
        return True
    return False

def _post_merge_short(clauses: List[str]) -> List[str]:
    if not clauses:
        return clauses

    def too_short(c: str) -> bool:
        if _has_domain_keyword(c):
            return False
        if re.fullmatch(r"[.!?]+", c.strip()):
            return True
        if re.fullmatch(r"[A-Za-zА-Яа-яЁё]\.?$", c.strip()):
            return True
        return len(_words_ru(c)) <= MIN_WORDS_SHORT_GLUE

    clean: List[str] = []
    i = 0
    while i < len(clauses):
        c = clauses[i].strip()
        is_connective = CONNECTIVE_ONLY.match(c) is not None
        short_or_low = too_short(c) or _is_low_content_clause(c)
        starts_subord = SUBORD_START.match(c) is not None and len(_words_ru(c)) <= (MIN_WORDS + 1)

        if is_connective or short_or_low or starts_subord or INTRO_PHRASES.match(c) or _is_parenthetical(c) or _is_money_short(c):
            if i + 1 < len(clauses):
                if _ends_sentence(c):
                    clean.append(c); i += 1; continue
                merged = DUP_CONNECTIVE.sub(r"\1", (c + " " + clauses[i + 1]).strip())
                clean.append(merged); i += 2; continue
            elif clean:
                clean[-1] = DUP_CONNECTIVE.sub(r"\1", (clean[-1] + " " + c).strip())
                i += 1; continue
            else:
                i += 1; continue

        c = re.sub(r"^(и|а|да и)\s+", "", c, flags=re.IGNORECASE)
        c = DUP_CONNECTIVE.sub(r"\1", re.sub(r"\s+", " ", c).strip(" ,;—-"))
        if c:
            clean.append(c)
        i += 1

    return [re.sub(r"\s+", " ", c).strip(" ,;—-") for c in clean if c.strip()]

def _final_prune(clauses: List[str]) -> List[str]:
    out: List[str] = []
    for c in clauses:
        c_stripped = re.sub(r"\s+", " ", c).strip(" ,;—-")

        if CONNECTIVE_ONLY.match(c_stripped):
            continue

        if _is_low_content_clause(c_stripped):
            if out:
                out[-1] = DUP_CONNECTIVE.sub(r"\1", (out[-1] + " " + c_stripped).strip(" ,;—-"))
            continue

        if (_is_money_short(c_stripped) or _is_parenthetical(c_stripped)) and out:
            out[-1] = DUP_CONNECTIVE.sub(r"\1", (out[-1] + " " + c_stripped).strip(" ,;—-"))
            continue

        if len(_words_ru(c_stripped)) < MIN_WORDS:
            if out and not _ends_sentence(out[-1]):
                out[-1] = DUP_CONNECTIVE.sub(r"\1", (out[-1] + " " + c_stripped).strip(" ,;—-"))
            else:
                pass
            continue

        out.append(c_stripped)

    cleaned: List[str] = []
    for c in out:
        if not cleaned or cleaned[-1] != c:
            cleaned.append(c)
    return cleaned

# =========================
# Основной пайплайн
# =========================

def split_into_clauses(text: str) -> List[str]:
    text = _normalize(text)
    text, mapping = _protect(text)

    clauses: List[str] = []
    for s in _split_sentences(text):
        for s2 in _split_by_quotes(s):
            for c in _split_by_contrast(s2):
                for c2 in _split_long_by_and(c):
                    clauses.extend(_split_by_commas(c2))

    clauses = _post_merge_short(clauses)
    clauses = [_unprotect(c, mapping) for c in clauses]

    cleaned: List[str] = []
    for c in clauses:
        c = re.sub(r"\s+", " ", c).strip(" ,;—-")
        if c and (not cleaned or cleaned[-1] != c):
            cleaned.append(c)

    cleaned = _final_prune(cleaned)
    return cleaned