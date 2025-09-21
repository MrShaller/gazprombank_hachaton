"""

Модуль для тематической классификации отзывов по клауза́м
с использованием словарей синонимов из configs/topics.yml.

Основная идея:
- Для каждой темы указываются ключевые слова (synonyms/include),
  стоп-слова (exclude) и возможные слова-соседи (cooccur).
- Каждая клауза проверяется регулярными выражениями на вхождение этих слов.
- На выходе для каждой клаузы сохраняются id предсказанных тем и их скоры.

Применение:
    from topic_matcher import label_dataframe
    df = label_dataframe(df, text_col="clause")

Выходные колонки:
- topics_pred  : id тем через `;`
- topics_score : скоры тем через `;`

"""

import re, yaml, pandas as pd
from typing import List, Dict, Any, Tuple

TOPICS_YML = "configs/topics.yml"

def _compile_token(token: str) -> re.Pattern:
    """
    Превращает строковый токен в регулярное выражение.
    
    - Если токен уже похож на regex (содержит спецсимволы) → берём как есть.
    - Если обычное слово/фраза → строим regex с поддержкой окончаний.
      Пример: "карта" → r"\bкарта\w*\b"
    """

    # если это уже regex (скобки/квантификаторы) — используем как есть
    if any(ch in token for ch in "().?+[]{}|"):
        pat = token
    else:
        # Разбиваем фразу на слова и разрешаем окончания для каждого
        words = token.split()
        pats = [rf"{re.escape(w)}\w*" for w in words]
        pat = r"\b" + r"\s+".join(pats) + r"\b"
    return re.compile(pat, flags=re.IGNORECASE | re.UNICODE)

def load_topics_cfg(path: str):
    """
    Загружает конфигурацию тем из YAML и компилирует regex-паттерны.

    Args:
        path (str): путь к topics.yml

    Returns:
        List[Dict[str, Any]]: список тем с их id, именем и регулярками
    """

    cfg = yaml.safe_load(open(path, encoding="utf-8"))
    topics = []
    for t in cfg["topics"]:
        include = t.get("include") or t.get("synonyms") or [] 
        exclude = t.get("exclude", [])
        cooccur = t.get("cooccur", [])
        topics.append({
            "id": t["id"],
            "name": t.get("name", t["id"]),
            "include_re": [_compile_token(x) for x in include],
            "exclude_re": [_compile_token(x) for x in exclude],
            "cooccur_re": [_compile_token(x) for x in cooccur],
        })
    return topics

def score_topic(text: str, topic: Dict[str, Any]) -> float:
    """
    Считает скор одной темы для данного текста.

    - exclude → если совпадение, сразу возвращаем -∞ (отсечение).
    - include → +1 за каждое совпадение.
    - cooccur → +0.5 за совпадение.

    Args:
        text (str): клауза
        topic (dict): описание темы

    Returns:
        float: суммарный скор
    """
    t = text.lower()
    # hard stop
    for r in topic["exclude_re"]:
        if r.search(t):
            return -1e9
    s = 0.0
    # include — основной сигнал
    inc_hits = sum(1 for r in topic["include_re"] if r.search(t))
    s += inc_hits * 1.0
    # cooccur — вспомогательный
    coc_hits = sum(1 for r in topic["cooccur_re"] if r.search(t))
    s += coc_hits * 0.5
    return s

def match_topics_for_clause(text: str, topics: List[Dict[str, Any]],
                            threshold: float = 1.0, top_k: int = 2) -> List[Tuple[str, float]]:
    """
    Возвращает список топ-N тем для клаузы.

    Args:
        text (str): клауза
        topics (list): список тем
        threshold (float): минимальный скор, ниже которого тема отбрасывается
        top_k (int): сколько тем максимум возвращать

    Returns:
        List[Tuple[str, float]]: [(id, score), ...]
    """

    scores = [(t["id"], score_topic(text, t)) for t in topics]
    scores = [(tid, sc) for tid, sc in scores if sc >= threshold]
    scores.sort(key=lambda x: x[1], reverse=True)
    # (опц.) margin, чтобы не брать слабую вторую тему
    if len(scores) >= 2 and scores[1][1] < scores[0][1] - 0.25:
        scores = scores[:1]
    return scores[:top_k]

def label_dataframe(df: pd.DataFrame, text_col: str = "clause",
                    threshold: float = 1.0, top_k: int = 2) -> pd.DataFrame:
    """
    Добавляет к DataFrame колонки с предсказанными темами.

    Args:
        df (pd.DataFrame): входной DataFrame
        text_col (str): имя колонки с текстом
        threshold (float): порог для темы
        top_k (int): сколько максимум тем присвоить

    Returns:
        pd.DataFrame: тот же df с новыми колонками topics_pred и topics_score
    """
    
    topics = load_topics_cfg(TOPICS_YML)
    out_labels, out_scores = [], []
    for txt in df[text_col].astype(str):
        hits = match_topics_for_clause(txt, topics, threshold=threshold, top_k=top_k)
        out_labels.append(";".join([h[0] for h in hits]))
        out_scores.append(";".join([f"{h[1]:.2f}" for h in hits]))
    res = df.copy()
    res["topics_pred"] = out_labels
    res["topics_score"] = out_scores
    return res

if __name__ == "__main__":
    # Демо-пример для быстрой проверки
    clauses = ["Крайне разочарована работой банка с клиентами.",
               "Писать им в чате тоже бесполезно."]
    df = pd.DataFrame({"clause": clauses})
    print(label_dataframe(df)[["clause", "topics_pred", "topics_score"]])
