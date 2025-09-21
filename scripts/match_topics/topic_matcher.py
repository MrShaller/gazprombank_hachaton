import re, yaml, pandas as pd
from typing import List, Dict, Any, Tuple

TOPICS_YML = "configs/topics.yml"

def _compile_token(token: str) -> re.Pattern:
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
    cfg = yaml.safe_load(open(path, encoding="utf-8"))
    topics = []
    for t in cfg["topics"]:
        include = t.get("include") or t.get("synonyms") or []  # <— вот ключевой момент
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
    scores = [(t["id"], score_topic(text, t)) for t in topics]
    scores = [(tid, sc) for tid, sc in scores if sc >= threshold]
    scores.sort(key=lambda x: x[1], reverse=True)
    # (опц.) margin, чтобы не брать слабую вторую тему
    if len(scores) >= 2 and scores[1][1] < scores[0][1] - 0.25:
        scores = scores[:1]
    return scores[:top_k]

def label_dataframe(df: pd.DataFrame, text_col: str = "clause",
                    threshold: float = 1.0, top_k: int = 2) -> pd.DataFrame:
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
    # пример: возьмём твои клаузы из списка
    clauses = [
        "Крайне разочарована работой банка с клиентами.",
        "Звонки по выделенной премиальной линии бесполезны - не дозвониться.",
        "Висела на телефоне ровно час- никто не брал трубку, а",
        "автоответчик все время повторял",
        "что осталась одна минута ожидания.",
        "так два раза по часу.",
        "Писать им в чате тоже бесполезно.",
        "Стандартный ответ \"Напишите или позвоните позже.",
        "Сейчас все операторы заняты\" По субботам и воскресеньям банк не работает и связаться с премиальным менеджером невозможно для решения срочных проблем.",
        "Так неужели нельзя",
        "бы по выходным обеспечить связь с банком по телефону или в чате.",
        "Что случилось? Уволили сотрудников?",
        "Раньше такого не было."
    ]
    df = pd.DataFrame({"clause": clauses})
    labeled = label_dataframe(df, "clause", threshold=1.0, top_k=2)
    print(labeled[["clause","topics_pred","topics_score"]].to_string(index=False))
