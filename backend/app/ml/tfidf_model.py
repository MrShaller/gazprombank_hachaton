import joblib
import numpy as np
import pandas as pd
from typing import List, Dict, Any
import logging
import time

logger = logging.getLogger(__name__)

class TfidfClassifier:
    def __init__(self, path: str):
        """Загружаем артефакты модели"""
        t0 = time.time()
        logger.info(f"[TFIDF] joblib.load start: {path}")
        artifacts = joblib.load(path)
        logger.info(f"[TFIDF] joblib.load done in {time.time() - t0:.3f}s")
        self.tfidf = artifacts["tfidf"]
        self.mlb = artifacts["mlb"]
        self.clf = artifacts["clf"]
        self.thresholds = artifacts["thresholds"]

        # вектор порогов (в порядке классов)
        self.thr_vec = np.array([self.thresholds[c] for c in self.mlb.classes_])
        logger.info(f"[TFIDF] classes: {len(self.mlb.classes_)} | thresholds: {len(self.thr_vec)}")

    def predict(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Возвращает список словарей по каждому тексту:
        {
          "labels": ["Дебетовая карта", "Обслуживание"],
          "labels_str": "Дебетовая карта, Обслуживание"
        }
        """
        t1 = time.time()
        logger.info(f"[TFIDF] transform start: n_texts={len(texts)}")
        X = self.tfidf.transform(texts)
        logger.info(f"[TFIDF] transform done in {time.time() - t1:.3f}s | shape={getattr(X, 'shape', None)}")
        t2 = time.time()
        Y_prob = self.clf.predict_proba(X)
        logger.info(f"[TFIDF] predict_proba done in {time.time() - t2:.3f}s")
        Y_pred = (Y_prob >= self.thr_vec).astype(int)
        labels = self.mlb.inverse_transform(Y_pred)

        results = []
        for labs in labels:
            labs = list(labs) if labs else []
            results.append({
                "labels": labs,
                "labels_str": ", ".join(labs) if labs else ""
            })
        return results

    def predict_dataframe(self, df: pd.DataFrame, text_col: str = "clause") -> pd.DataFrame:
        """Добавляет в DataFrame колонку pred"""
        preds = self.predict(df[text_col].astype(str).tolist())
        df = df.copy()
        df["pred"] = [p["labels_str"] for p in preds]
        return df
