import sys
import types
import pandas as pd
from backend.app.ml.pipeline import InferencePipeline
from backend.app.ml.utils import tokenize_lemma

# --- фикс для joblib (ожидает tokenize_lemma в старом месте) ---
fake_module = types.ModuleType("scripts.models.inference_pipeline")
fake_module.tokenize_lemma = tokenize_lemma
sys.modules["scripts.models.inference_pipeline"] = fake_module

CSV_PATH = "data/interim/clauses.csv"
OUT_CLAUSES = "data/processed/result_clauses.csv"
OUT_FINAL   = "data/processed/result_final.csv"

# инициализация пайплайна
pipe = InferencePipeline(
    tfidf_path="models/tfidf_lr/model.pkl",
    xlmr_path="models/xlmr"
)

# читаем данные (для теста только первые 40)
df = pd.read_csv(CSV_PATH).head(40)

# 1️⃣ Поклаузные предсказания
#res_clauses = pipe.run(df)
#res_clauses.to_csv(OUT_CLAUSES, index=False)
#print(f"✅ Результат по клауза́м сохранён в {OUT_CLAUSES}")

# 2️⃣ Финальная агрегация по review_id
res_final = pipe.run_and_aggregate(df)
res_final.to_csv(OUT_FINAL, index=False)
print(f"✅ Финальный результат сохранён в {OUT_FINAL}")
