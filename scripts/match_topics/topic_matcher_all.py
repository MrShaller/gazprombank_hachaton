# scripts/topic_match_all.py
import pandas as pd
from topic_matcher import label_dataframe  # это твой файл scripts/topic_matcher.py

IN_PATH  = "data/interim/clauses.csv"
OUT_PATH = "data/interim/clauses_with_topics.csv"

TEXT_COL = "clause"   # у тебя колонка так и называется

def main(threshold=1.0, top_k=2, chunksize=10000):
    # Если файл небольшой — можно без чанков:
    # df = pd.read_csv(IN_PATH)
    # labeled = label_dataframe(df, text_col=TEXT_COL, threshold=threshold, top_k=top_k)
    # labeled.to_csv(OUT_PATH, index=False, encoding="utf-8")

    # Вариант с чанками — безопасно для больших файлов
    first = True
    for chunk in pd.read_csv(IN_PATH, chunksize=chunksize):
        labeled = label_dataframe(chunk, text_col=TEXT_COL,
                                  threshold=threshold, top_k=top_k)
        labeled.to_csv(OUT_PATH, index=False, mode="w" if first else "a",
                       header=first, encoding="utf-8")
        first = False
    print(f"[topic_match_all] wrote → {OUT_PATH}")

if __name__ == "__main__":
    main()
