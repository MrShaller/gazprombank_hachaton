import sys
import types
import pandas as pd
from backend.app.ml.pipeline import InferencePipeline
from backend.app.ml.utils import tokenize_lemma

# --- фикс для joblib (ожидает tokenize_lemma в старом месте) ---
fake_module = types.ModuleType("scripts.models.inference_pipeline")
fake_module.tokenize_lemma = tokenize_lemma
sys.modules["scripts.models.inference_pipeline"] = fake_module

OUT_FINAL = "data/processed/result_final.json"

# инициализация пайплайна
pipe = InferencePipeline(
    tfidf_path="models/tfidf_lr/model.pkl",
    xlmr_path="models/xlmr"
)

# 🔹 тестовые данные (обычно приходят из запроса в FastAPI)
sample_json = [
    {"id": 1, "text": "Банк обманул меня с начислением кешбэка!"},
    {"id": 2, "text": "Поддержка работает замечательно, но карта ужасная."},
    {"id": 3, "text": 'Пришла в отделение, думала буду долго ждать и долго оформлять, в итоге провела в отделении минут 10 и ушла с решенной проблемой, быстро, четко, приятно) спасибо. Проблема была в том, что из за мошеничских действий заблокировалось приложение и все счета. Пришла в отделение в 17.00 передо мной было 2 человека, думала просижу долго, но нет, все прошло быстро.'}
]
# 🔹 читаем тестовый JSON
#with open("data/raw/test_request2.json", "r", encoding="utf-8") as f:
#    raw = json.load(f)

# достаем список
#sample_json = raw["data"]
# 1️⃣ Поклаузные предсказания из JSON
df_clauses = pipe.run_from_json(sample_json)
print("=== Поклаузные предсказания ===")
print(df_clauses.head())

# 2️⃣ Финальная агрегация из JSON
df_final = pipe.run_and_aggregate_from_json(sample_json)
print("=== Финальная агрегация ===")
print(df_final.head())

# можно сохранить в JSON
df_final.to_json(OUT_FINAL, orient="records", force_ascii=False, indent=2)
print(f"✅ Финальный результат сохранён в {OUT_FINAL}")