import joblib
import numpy as np
import pandas as pd
from typing import List, Dict, Any

class TfidfClassifier:
    def __init__(self, path: str):
        """Загружаем артефакты модели"""
        artifacts = joblib.load(path)
        self.tfidf = artifacts["tfidf"]
        self.mlb = artifacts["mlb"]
        self.clf = artifacts["clf"]
        self.thresholds = artifacts["thresholds"]

        # вектор порогов (в порядке классов)
        self.thr_vec = np.array([self.thresholds[c] for c in self.mlb.classes_])

    def predict(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Возвращает список словарей по каждому тексту:
        {
          "labels": ["Дебетовая карта", "Обслуживание"],
          "labels_str": "Дебетовая карта, Обслуживание"
        }
        """
        X = self.tfidf.transform(texts)
        Y_prob = self.clf.predict_proba(X)
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
