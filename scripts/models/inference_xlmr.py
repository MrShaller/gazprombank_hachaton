import pandas as pd
import torch
from backend.app.ml.xlmr_model import load_pretrained, predict
from backend.app.ml.xlmr_postprocess import postprocess

MODEL_PATH = "models/xlmr"
CSV_PATH   = "data/interim/clauses.csv"
OUT_PATH   = "data/processed/test_xlmr_40.csv"

device = "cuda" if torch.cuda.is_available() else "cpu"
print('device:', device)
tok, mdl, cfg = load_pretrained(MODEL_PATH, device)


df = pd.read_csv(CSV_PATH).head(40)
preds, probs = predict(df["clause"].astype(str).tolist(), tok, mdl, max_len=cfg.get("max_len", 128), device=device)

res = postprocess(preds, probs, df, cfg["classes"], cfg["id2sent"], tau=0.5)
res.to_csv(OUT_PATH, index=False)

print("✅ Результат сохранён в", OUT_PATH)
