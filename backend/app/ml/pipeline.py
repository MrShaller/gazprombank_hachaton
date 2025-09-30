import pandas as pd
from collections import Counter
from .tfidf_model import TfidfClassifier
from .xlmr_model import load_pretrained, predict
from .xlmr_postprocess import postprocess
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from scripts.clause.splitter import split_into_clauses
import torch


def parse_pred_bert(pred_str):
    if not isinstance(pred_str, str):
        return []
    pairs = []
    for part in pred_str.split("|"):
        if ":" in part:
            topic, sentiment = part.split(":", 1)
            pairs.append((topic.strip(), sentiment.strip()))
    return pairs


def aggregate_sentiments(sentiments):
    cnt = Counter(sentiments)
    pos, neg, neu = cnt.get("положительно", 0), cnt.get("отрицательно", 0), cnt.get("нейтрально", 0)

    if pos > neg and pos >= neu:
        return "положительно"
    elif neg > pos and neg >= neu:
        return "отрицательно"
    elif neu > pos and neu > neg:
        return "нейтрально"
    else:
        if pos == neg and pos > 0:
            return "нейтрально"
        if pos > 0 and neu > 0 and pos >= neu:
            return "положительно"
        if neg > 0 and neu > 0 and neg >= neu:
            return "отрицательно"
        return "нейтрально"


def parse_pred_tfidf(pred_str):
    if not isinstance(pred_str, str):
        return []
    return [t.strip() for t in pred_str.split(",") if t.strip()]


class InferencePipeline:
    def __init__(self, tfidf_path: str, xlmr_path: str, device=None):
        self.tfidf = TfidfClassifier(tfidf_path)
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.tok, self.mdl, self.cfg = load_pretrained(xlmr_path, self.device)

    def preprocess_json(self, data: list[dict]) -> pd.DataFrame:
        rows = []
        for rec in data:
            text = rec.get("text", "")
            review_id = rec.get("id")
            clauses = split_into_clauses(text) or [text.strip()]
            for i, cl in enumerate(clauses):
                rows.append({
                    "review_id": review_id,
                    "clause_id": i,
                    "clause": cl.strip()
                })
        return pd.DataFrame(rows)
    
    def run_from_json(self, data: list[dict]) -> pd.DataFrame:
        df = self.preprocess_json(data)
        return self.run(df)

    def run_and_aggregate_from_json(self, data: list[dict]) -> pd.DataFrame:
        df = self.preprocess_json(data)
        return self.run_and_aggregate(df)

    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        # TF-IDF
        tfidf_res = self.tfidf.predict_dataframe(df, text_col="clause")
        tfidf_res = tfidf_res.rename(columns={"pred": "pred_tfidf"})

        # XLM-R
        preds, probs = predict(
            df["clause"].astype(str).tolist(),
            self.tok,
            self.mdl,
            max_len=self.cfg.get("max_len", 128),
            device=self.device
        )
        xlmr_res = postprocess(preds, probs, df, self.cfg["classes"], self.cfg["id2sent"], tau=0.5)
        xlmr_res = xlmr_res.rename(columns={"pred_pairs": "pred_bert"})

        # объединение по review_id + clause_id
        merged = pd.merge(
            xlmr_res[["review_id", "clause_id", "clause", "pred_bert"]],
            tfidf_res[["review_id", "clause_id", "pred_tfidf"]],
            on=["review_id", "clause_id"],
            how="inner"
        )
        return merged

    def run_and_aggregate(self, df: pd.DataFrame) -> pd.DataFrame:
        merged = self.run(df)

        # --- агрегируем BERT ---
        agg_rows = []
        for rid, group in merged.groupby("review_id"):
            topic_sentiments = {}
            for _, row in group.iterrows():
                for topic, sent in parse_pred_bert(row["pred_bert"]):
                    topic_sentiments.setdefault(topic, []).append(sent)
            agg = {topic: aggregate_sentiments(sents) for topic, sents in topic_sentiments.items()}
            agg_rows.append({"review_id": rid, "pred_agg": agg})
        agg_df = pd.DataFrame(agg_rows)

        # --- агрегируем TF-IDF ---
        agg_rows_tfidf = []
        for rid, group in merged.groupby("review_id"):
            all_topics = []
            for _, row in group.iterrows():
                all_topics.extend(parse_pred_tfidf(row["pred_tfidf"]))
            agg_rows_tfidf.append({
                "review_id": rid,
                "pred_tfidf_agg": sorted(set(all_topics))
            })
        agg_tfidf_df = pd.DataFrame(agg_rows_tfidf)

        # --- финальное объединение ---
        final = pd.merge(df[["review_id", "clause_id", "clause"]], merged, on=["review_id", "clause_id"], how="left")
        final = pd.merge(final, agg_df, on="review_id", how="left")
        final = pd.merge(final, agg_tfidf_df, on="review_id", how="left")

        # extra topics
        def find_extra_topics_row(row):
            bert_topics = set(row["pred_agg"].keys()) if isinstance(row["pred_agg"], dict) else set()
            tfidf_topics = set(row["pred_tfidf_agg"]) if isinstance(row["pred_tfidf_agg"], list) else set()
            return list(tfidf_topics - bert_topics)

        final["extra"] = final.apply(find_extra_topics_row, axis=1)

        return final
