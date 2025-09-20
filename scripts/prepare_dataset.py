# scripts/prepare_dataset.py
import os
import csv
import json
import hashlib
from pathlib import Path
from typing import Dict, Iterable, List, Any

# импорт твоего сплиттера
from clause.splitter import split_into_clauses

RAW_DIR = Path("data/raw")
OUT_PATH = Path("data/interim/clauses.csv")

# --- простая очистка без агрессии (не выкидываем "не/но/однако") ---
def light_clean(text: str) -> str:
    if not isinstance(text, str):
        return ""
    t = text.replace("\u00A0", " ")
    t = " ".join(t.split())
    return t.strip()

# --- безопасная выборка полей с учётом опечаток ---
def get_field(rec: Dict[str, Any], names: List[str], default=None):
    for n in names:
        if n in rec and rec[n] not in (None, ""):
            return rec[n]
    return default

def ensure_review_id(rec: Dict[str, Any]) -> str:
    rid = get_field(rec, ["review_id", "rewied_id", "rewiew_id", "id", "reviewId"])
    if rid is None:
        # генерируем стабильный id из хэша текста+url+parsed_at
        src = f"{get_field(rec,['rewiew_text','review_text','text'],'')}-{get_field(rec,['url'],'')}-{get_field(rec,['parsed_at'],'')}"
        rid = hashlib.sha1(src.encode("utf-8")).hexdigest()[:16]
    return str(rid)

def iter_raw_records(path: Path) -> Iterable[Dict[str, Any]]:
    """
    Поддерживает:
    - JSON массив: [ {...}, {...} ]
    - JSONL: по строке на запись
    """
    if path.suffix.lower() in [".jsonl", ".jl"]:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                yield json.loads(line)
    elif path.suffix.lower() == ".json":
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            # если вдруг словарь с ключом data
            data = data.get("data", [])
        for obj in data:
            yield obj
    else:
        raise ValueError(f"Unsupported file: {path}")

def prepare_one_file(file_path: Path, writer: csv.DictWriter, batch_size: int = 200):
    batch_rows = []
    for rec in iter_raw_records(file_path):
        text = get_field(rec, ["rewiew_text", "review_text", "text"], "")
        if not text or not isinstance(text, str):
            continue

        review_id = ensure_review_id(rec)
        url = get_field(rec, ["url"], "")
        parsed_at = get_field(rec, ["parsed_at", "parsedAt"], "")
        bank_name = get_field(rec, ["bank_name", "bankName"], "")
        product_type = get_field(rec, ["product_type", "productType"], "")

        clauses = split_into_clauses(text)
        for i, cl in enumerate(clauses):
            row = {
                "source_file": file_path.name,
                "review_id": review_id,
                "clause_id": i,
                "global_id": f"{review_id}:{i}",
                "clause": light_clean(cl),  # или без clean, как хочешь
            }
            batch_rows.append(row)

        # сброс батча
        if len(batch_rows) >= batch_size:
            writer.writerows(batch_rows)
            batch_rows.clear()

    # финальный сброс
    if batch_rows:
        writer.writerows(batch_rows)

def main():
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # если файла нет — создаём с заголовком; если есть — перезапишем (чистый старт)
    fieldnames = [
    "source_file", "review_id", "clause_id", "global_id",
    "clause"   # одна колонка
    ]
    with OUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        # прогоняем 1 файл (и задел на будущее — все файлы каталога)
        raw_files = []
        # прицельно 1.json
        one = RAW_DIR / "1.json"
        if one.exists():
            raw_files.append(one)
        # на будущее — собрать все *.json/jsonl
        for p in RAW_DIR.glob("*.json"):
            if p != one:
                raw_files.append(p)
        for p in RAW_DIR.glob("*.jsonl"):
            raw_files.append(p)

        for fp in raw_files:
            print(f"[prepare_dataset] Processing {fp} ...")
            prepare_one_file(fp, writer, batch_size=500)

    print(f"[prepare_dataset] Done. Wrote: {OUT_PATH}")

if __name__ == "__main__":
    main()
