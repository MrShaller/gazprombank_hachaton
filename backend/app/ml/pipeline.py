import pandas as pd
from collections import Counter
from .tfidf_model import TfidfClassifier
from .xlmr_model import load_pretrained, predict
from .xlmr_postprocess import postprocess
import sys
import os
import time
import logging
import re
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from scripts.clause.splitter import split_into_clauses
import torch

logger = logging.getLogger(__name__)


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


# --- Доп. правила обогащения тем TF-IDF и назначение тональности ---
def is_money_transfer_context(text: str) -> bool:
    text = text.lower()
    sentences = re.split(r"[.,!?]", text)
    for sent in sentences:
        sent = sent.strip()
        if "деньг" in sent and re.search(r"\bперев\w*", sent):
            return True
    return False


def is_debit_card_context(text: str) -> bool:
    text = text.lower()
    # исключаем кредитки
    if re.search(r"кредитн\w*\s+карт", text):
        return False
    # исключаем контекст переводов/СБП
    transfer_bad = [
        "сбп", "система быстрых платежей", "перевод", "перевела",
        "перевел", "перевести", "операция не прошла", "деньги не дошли", "не поступил"
    ]
    if any(tb in text for tb in transfer_bad):
        return False
    # прямые упоминания получения карты
    if re.search(r"(привез\w*|достав\w*|оформ\w*|выпуст\w*|получил\w*|получить готовую)\s+карт", text):
        return True
    # карта + название банка
    if re.search(r"карт\w*\s+(газпром|сбер|тинькоф|втб|альфа|росбанк)", text):
        return True
    # явное упоминание дебетовой
    if re.search(r"дебетов\w*\s+карт", text):
        return True
    tokens = text.split()
    for i, tok in enumerate(tokens):
        if tok.startswith("карт"):
            left = tokens[max(0, i - 2):i]
            right = tokens[i + 1:i + 3]
            context = " ".join(left + right)
            bad_words = ["перевел", "перевела", "перевести", "снять", "снял", "сняла", "деньги", "на", "с"]
            if any(bad in context for bad in bad_words):
                return False
            good_words = [
                "дебетова", "сберкарта", "пластиковая", "зарплатная", "газпромбанк",
                "заблокир", "разблокир", "лимит", "одобр", "закрыл", "открыл",
                "привез", "достав", "оформ", "выпуст", "получил"
            ]
            if any(good in text for good in good_words):
                return True
            if "карты были" in text or "карты заблокированы" in text:
                return True
    return False


RULES = {
    "Автокредит": {"include": ["автокредит", "кредит на машину", "машина в кредит"], "exclude": []},
    "Вклады": {"include": ["вклад", "вклады", "вклада", "накопительный счет"], "exclude": []},
    "Дебетовая карта": {
        "include": ["карта", "карты", "карта газпромбанка"],
        "exclude": ["кредитная карта", "кредит", "кредитную карту"],
        "custom": "is_debit_card_context",
    },
    "Другое": {
        "include": [
            "кэшбек", "баллы", "бонус", "сертификат", "акция", "подарок", "зарплатный клиент",
            "премиум клиент", "обмен валют"
        ],
        "exclude": [],
    },
    "Потребительский кредит": {
        "include": [
            "потребительский кредит", "кредит наличными", "взял кредит", "оформил кредит",
            "потребкредит", "при оформлении кредита", "о кредите", "кредиторов", "кредитор",
            "кредиторы", "график платежей"
        ],
        "exclude": ["ипотек", "автокредит", "машин", "льготный период", "минимальный платеж", "кредитная карта"],
    },
    "Ипотека": {"include": ["ипотечному кредитованию", "ипотечное кредитование", "ипотека"], "exclude": []},
    "Денежные переводы": {"include": [], "exclude": [], "custom": "is_money_transfer_context"},
    "Рефинансирование кредитов": {
        "include": [
            "рефинансирование", "рефинансирован", "рефинансирование кредита", "рефинансировать кредит",
            "объединение кредитов", "перекредитоваться", "новый кредит для погашения старого"
        ],
        "exclude": [],
    },
    "Обслуживание": {
        "include": [
            "приехала вовремя", "приехал вовремя", "курьер привезла карту", "курьер привез карту",
            "при визите в банк", "отвратительный сервис", "обслуживание в офисе"
        ],
        "exclude": [],
    },
    "Дистанционное обслуживание": {
        "include": [
            "обратилась в чат", "провисев на линии", "в чате другой консультант", "уточнил в техподдержке",
            "в техподдержке сказали", "обратились в поддержку", "пообщался с оператором", "позвонила в газпром",
            "на горячей линии", "в службу поддержки", "в службе поддержки", "в контактный центр",
            "позвонила в банк", "соединили с оператором", "но оператор", "возразить в чате", "звонил в газпромбанк",
            "в чате оператор", "по телефону"
        ],
        "exclude": [],
    },
}


def choose_sentiment_for_new_topic(bert_agg: dict) -> str:
    """Назначить тональность новой теме на основе общей картины BERT.
    Логика: если есть только одна полярность — её и берём; при смешении положит./отрицат. → нейтрально.
    При отсутствии — нейтрально.
    """
    if not isinstance(bert_agg, dict) or not bert_agg:
        return "нейтрально"
    sentiments = list(bert_agg.values())
    return aggregate_sentiments(sentiments)


def apply_rules_to_row(row) -> dict:
    text = str(row.get("text", ""))
    bert_agg = row.get("pred_agg") or {}
    tfidf_topics = set(row.get("pred_tfidf_agg") or [])
    bert_topics = set(bert_agg.keys()) if isinstance(bert_agg, dict) else set()
    extra_topics = tfidf_topics - bert_topics

    new_classes = {}
    already_has_credit = "Кредитная карта" in bert_topics
    already_has_refi_or_credit = any(cls in bert_topics for cls in ["Рефинансирование кредитов", "Кредитная карта"])

    for cls, rule in RULES.items():
        if cls not in extra_topics:
            continue
        # защита от конфликтов
        if cls == "Дебетовая карта" and already_has_credit:
            continue
        if cls == "Потребительский кредит" and already_has_refi_or_credit:
            continue
        passed = False
        if "custom" in rule:
            if rule["custom"] == "is_debit_card_context" and is_debit_card_context(text):
                passed = True
            if rule["custom"] == "is_money_transfer_context" and is_money_transfer_context(text):
                passed = True
        else:
            low = text.lower()
            ok_include = any(kw in low for kw in rule.get("include", [])) if rule.get("include") else False
            ok_exclude = all(kw not in low for kw in rule.get("exclude", [])) if rule.get("exclude") else True
            passed = ok_include and ok_exclude
        if passed:
            new_classes[cls] = choose_sentiment_for_new_topic(bert_agg)

    updated = dict(bert_agg) if isinstance(bert_agg, dict) else {}
    updated.update(new_classes)
    return updated


class InferencePipeline:
    def __init__(self, tfidf_path: str, xlmr_path: str, device=None):
        logger.info(f"[PIPELINE] start")
        t0 = time.time()
        logger.info(f"[PIPELINE] Init start | tfidf_path={tfidf_path} xlmr_path={xlmr_path}")
        # TF-IDF load
        t_load_tfidf = time.time()
        self.tfidf = TfidfClassifier(tfidf_path)
        logger.info(f"[PIPELINE] TF-IDF loaded in {time.time() - t_load_tfidf:.3f}s")

        # XLM-R load
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        t_load_xlmr = time.time()
        self.tok, self.mdl, self.cfg = load_pretrained(xlmr_path, self.device)
        logger.info(f"[PIPELINE] XLM-R loaded on {self.device} in {time.time() - t_load_xlmr:.3f}s")
        logger.info(f"[PIPELINE] Init done in {time.time() - t0:.3f}s")

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
        """
        Принимаем список словарей [{"id": ..., "text": ...}, ...]
        Возвращаем агрегированный результат по каждому отзыву
        """
        # сохраняем оригинальные тексты для объединения
        reviews = pd.DataFrame(data).rename(columns={"id": "review_id"})

        # режем на клаузы
        t_prep = time.time()
        df = self.preprocess_json(data)
        logger.info(f"[PIPELINE] Preprocess: {len(df)} clauses from {len(reviews)} reviews in {time.time() - t_prep:.3f}s")

        # запускаем инференс
        t_run = time.time()
        merged = self.run(df)
        logger.info(f"[PIPELINE] run() produced {len(merged)} rows in {time.time() - t_run:.3f}s")

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

        # --- объединяем с исходными текстами ---
        final = pd.merge(reviews.rename(columns={"text": "text"}), agg_df, on="review_id", how="left")
        final = pd.merge(final, agg_tfidf_df, on="review_id", how="left")

        # --- применяем правила к новым темам из TF-IDF ---
        t_rules = time.time()
        final["pred_agg_rules"] = final.apply(lambda r: apply_rules_to_row(r), axis=1)
        final["added_by_rules"] = final.apply(lambda r: list(set((r.get("pred_agg_rules") or {}).keys()) - set((r.get("pred_agg") or {}).keys() if isinstance(r.get("pred_agg"), dict) else set())), axis=1)
        logger.info(f"[PIPELINE] rules applied in {time.time() - t_rules:.3f}s")

        # --- находим extra topics ---
        #def find_extra_topics_row(row):
        #    bert_topics = set(row["pred_agg"].keys()) if isinstance(row["pred_agg"], dict) else set()
        #    tfidf_topics = set(row["pred_tfidf_agg"]) if isinstance(row["pred_tfidf_agg"], list) else set()
        #    return list(tfidf_topics - bert_topics)

        #final["extra"] = final.apply(find_extra_topics_row, axis=1)

        return final

    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        # TF-IDF
        t_tfidf = time.time()
        logger.info(f"[PIPELINE] TF-IDF start on {len(df)} clauses")
        tfidf_res = self.tfidf.predict_dataframe(df, text_col="clause")
        tfidf_res = tfidf_res.rename(columns={"pred": "pred_tfidf"})
        logger.info(f"[PIPELINE] TF-IDF done in {time.time() - t_tfidf:.3f}s")

        # XLM-R
        t_xlmr = time.time()
        logger.info(f"[PIPELINE] XLM-R start on {len(df)} clauses (max_len={self.cfg.get('max_len', 128)})")
        preds, probs = predict(
            df["clause"].astype(str).tolist(),
            self.tok,
            self.mdl,
            max_len=self.cfg.get("max_len", 128),
            device=self.device
        )
        logger.info(f"[PIPELINE] XLM-R predict done in {time.time() - t_xlmr:.3f}s")
        t_post = time.time()
        xlmr_res = postprocess(preds, probs, df, self.cfg["classes"], self.cfg["id2sent"], tau=0.5)
        xlmr_res = xlmr_res.rename(columns={"pred_pairs": "pred_bert"})
        logger.info(f"[PIPELINE] XLM-R postprocess done in {time.time() - t_post:.3f}s")

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
