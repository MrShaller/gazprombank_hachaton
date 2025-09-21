# -*- coding: utf-8 -*-
import pandas as pd
from sentiment_rules import score_clause

IN_PATH  = "data/interim/clauses_with_topics.csv"
OUT_PATH = "data/interim/clauses_with_topics_sentiment.csv"

# Весовая смесь: clause 70% + review 30%
W_CLAUSE = 0.70
W_REVIEW = 0.30

# Бининг в {-2, -1, 0, +1, +2}
def bin_to_five(score: float) -> int:
    if score >= 1.5:
        return  2
    if score >= 0.75:
        return  1
    if score <= -1.5:
        return -2
    if score <= -0.75:
        return -1
    return 0

def text_label(v: int) -> str:
    if v > 0:  return "pos"
    if v < 0:  return "neg"
    return "neu"

def main():
    df = pd.read_csv(IN_PATH)
    required = {"review_id", "clause_id", "clause"}
    miss = required - set(df.columns)
    if miss:
        raise ValueError(f"Missing required columns: {miss}")

    # 1) Локальный скор по каждой клауза
    df["sent_local"] = df["clause"].astype(str).map(score_clause)

    # 2) Общий тон по отзыву = средний по клауза́м (можно медиану)
    review_mean = df.groupby("review_id", sort=False)["sent_local"].mean().rename("sent_review")
    df = df.merge(review_mean, on="review_id", how="left")

    # 3) Смешиваем: final = 0.7*local + 0.3*review
    df["sentiment_score"] = W_CLAUSE * df["sent_local"] + W_REVIEW * df["sent_review"]

    # 4) В бины {-2..+2} и текстовую метку
    df["sentiment_final"] = df["sentiment_score"].map(bin_to_five).astype(int)
    df["sentiment_text"]  = df["sentiment_final"].map(text_label)

    # (опц.) если хочешь считать тон только когда есть тема:
    # mask_has_topic = df["topics_pred"].fillna("").str.len() > 0
    # df.loc[~mask_has_topic, ["sentiment_score", "sentiment_final", "sentiment_text"]] = [0.0, 0, "neu"]

    # 5) Сохраняем
    keep_cols = list(df.columns)  # ничего не теряем
    df.to_csv(OUT_PATH, index=False, encoding="utf-8", columns=keep_cols)
    print(f"[sentiment_predict_all] wrote → {OUT_PATH}")

if __name__ == "__main__":
    main()
