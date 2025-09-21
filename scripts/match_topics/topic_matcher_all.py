"""

Скрипт для пакетной тематической разметки клауз (кусочков отзывов).
Читает входной CSV с клауза́ми, проставляет предсказанные темы по словарю
из configs/topics.yml, и записывает результат в новый CSV.

Вход:  data/interim/clauses.csv
Выход: data/interim/clauses_with_topics.csv

Колонки на выходе:
- topics_pred  : id тем (строка, разделитель `;`)
- topics_score : числовые скоры (строка, разделитель `;`)

"""

import pandas as pd
from topic_matcher import label_dataframe

IN_PATH  = "data/interim/clauses.csv"
OUT_PATH = "data/interim/clauses_with_topics.csv"

TEXT_COL = "clause" 

def main(threshold=1.0, top_k=2, chunksize=10000):
    """
    Основная функция пакетной обработки.

    Args:
        threshold (float): минимальный порог скора темы (темы с меньшим отбрасываются).
        top_k (int): сколько максимум тем сохранять для одной клаузы.
        chunksize (int): сколько строк CSV читать за один раз (для экономии памяти).

    Workflow:
        1. Читаем clauses.csv порциями (chunksize строк).
        2. Для каждой порции применяем label_dataframe().
        3. Сохраняем результат в clauses_with_topics.csv (построчно дозаписываем).
    """
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
