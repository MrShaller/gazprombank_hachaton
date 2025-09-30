import pandas as pd
import sys

from backend.app.ml.tfidf_model import TfidfClassifier
from backend.app.ml.utils import tokenize_lemma

# создаём фиктивный модуль и подсовываем туда функцию
import types
fake_module = types.ModuleType("scripts.models.inference_tfidf")
fake_module.tokenize_lemma = tokenize_lemma
sys.modules["scripts.models.inference_tfidf"] = fake_module

# пути
MODEL_PATH = "models/tfidf_lr/model.pkl"
CSV_PATH   = "data/interim/clauses.csv"

# загружаем модель
clf = TfidfClassifier(MODEL_PATH)

# читаем данные
df = pd.read_csv(CSV_PATH)

# берём только первые 40
#df_sample = df.head(40)

# предсказываем
res = clf.predict_dataframe(df, text_col="clause")

# печатаем в консоль
print(res[["clause", "pred"]])

# можно сохранить для отладки
res.to_csv("data/processed/test_tfidf_40.csv", index=False)
print("✅ Результат сохранён в data/processed/test_tfidf_40.csv")