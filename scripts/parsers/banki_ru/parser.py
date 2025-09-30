import re
import time
import json
import csv
from dataclasses import dataclass, asdict
from typing import List, Optional
from urllib.parse import urljoin, urlsplit, urlunsplit, parse_qsl, urlencode
import requests
from bs4 import BeautifulSoup
import random
import os
from datetime import datetime

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ===================== CONFIG =====================
BASE = "https://www.banki.ru"

# Категория: Ипотека
LIST_URL = "https://www.banki.ru/services/responses/bank/gazprombank/product/debitcards/?type=all"
product_type = "Дебетовые карты"

# Куда сохранять
RAW_DIR = "/Users/mishantique/Desktop/Projects/gazprombank_hachaton/data/raw/banki_ru"
os.makedirs(RAW_DIR, exist_ok=True)

# Временной фильтр (включительно)
DATE_FROM = datetime(2024, 1, 1, 0, 0, 0)
DATE_TO   = datetime(2025, 5, 31, 23, 59, 59)
# ==================================================


def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/127.0.0.0 Safari/537.36"),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.7,en;q=0.6",
        "Referer": "https://www.banki.ru/",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    })
    retry = Retry(total=5, connect=3, read=3, backoff_factor=0.6,
                  status_forcelist=[429, 500, 502, 503, 504],
                  allowed_methods=["HEAD", "GET", "OPTIONS"])
    adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s


SESSION = make_session()


@dataclass
class ParsedReview:
    review_id: str
    review_text: str
    review_date: str
    url: str
    parsed_at: str
    bank_name: str = "gazprombank"
    product_type: Optional[str] = None
    rating: Optional[int] = None
    tonality: Optional[str] = None
    validation: Optional[str] = None
    is_valid: Optional[bool] = None


@dataclass
class Review:
    title: str
    date: str
    rating: Optional[int]
    author: Optional[str]
    location: Optional[str]
    text: str
    url: str
    bank_response_date: Optional[str] = None
    bank_response_text: Optional[str] = None
    date_dt: Optional[datetime] = None
    validation: Optional[str] = None
    is_valid: Optional[bool] = None


@dataclass
class Category:
    url: str
    product_type: str
    start_page: int = 677
    max_pages: int = 1200
    backup_prefix: Optional[str] = None
    file_name: Optional[str] = None  # имя файла без .json


def set_page_param(url: str, page: int) -> str:
    u = urlsplit(url)
    pairs = parse_qsl(u.query, keep_blank_values=True)
    pairs = [(k, v) for (k, v) in pairs if k != "page"]
    new_pairs = [("page", str(page))] + pairs
    return urlunsplit((u.scheme, u.netloc, u.path, urlencode(new_pairs, doseq=True), ""))


def parse_review_datetime(s: str) -> Optional[datetime]:
    s = (s or "").strip()
    m = re.search(r"\b(\d{2})\.(\d{2})\.(\d{4})\s+(\d{2}):(\d{2})\b", s)
    if m:
        d, mo, y, hh, mm = map(int, m.groups())
        try: return datetime(y, mo, d, hh, mm)
        except ValueError: return None
    m2 = re.search(r"\b(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})", s)
    if m2:
        y, mo, d, hh, mm = map(int, m2.groups())
        try: return datetime(y, mo, d, hh, mm)
        except ValueError: return None
    return None


def tonality_by_rating(r: Optional[int]) -> Optional[str]:
    if r is None: return None
    if r in (1, 2): return "отрицательно"
    if r == 3: return "нейтрально"
    if r in (4, 5): return "положительно"
    return None


def extract_validation(norm_text: str) -> tuple[Optional[str], Optional[bool]]:
    if "Отзыв проверен" in norm_text:
        return "Отзыв проверен", True
    if "Отзыв проверяется" in norm_text:
        return "Отзыв проверяется", False
    return None, None


RE_VIEW = re.compile(r'/services/responses/bank/response/\d+/?', re.I)


def get(url: str, referer: str | None = None) -> BeautifulSoup:
    timeout = (10, 60)
    headers = {"Referer": referer} if referer else {}
    resp = SESSION.get(url, timeout=timeout, headers=headers)
    resp.raise_for_status()
    html = resp.text
    if not html or len(html) < 1500:
        time.sleep(1.2 + random.random())
        resp = SESSION.get(url, timeout=timeout, headers=headers)
        resp.raise_for_status()
        html = resp.text
    return BeautifulSoup(html, "lxml")


def extract_review_links(soup, reverse=False) -> list[str]:
    seen, links = set(), []
    for a in soup.select('a[href*="/services/responses/bank/response/"]'):
        href = (a.get("href") or "").split("#")[0]
        if "/services/responses/bank/response/" in href:
            url = urljoin(BASE, href)
            if url not in seen:
                seen.add(url); links.append(url)
    if len(links) < 3:
        raw = soup.decode()
        for m in RE_VIEW.finditer(raw):
            url = urljoin(BASE, m.group(0))
            if url not in seen:
                seen.add(url); links.append(url)
    if reverse: links.reverse()
    return links


def extract_rating(soup: BeautifulSoup, norm_text: str) -> Optional[int]:
    for el in soup.select(".rating-grade, [class*='rating-grade']"):
        txt = el.get_text(strip=True)
        m = re.search(r"\b([1-5])\b", txt)
        if m: return int(m.group(1))
    for patt in (r"Оценка\s*([1-5])\b", r"Оценка\D{0,10}([1-5])\b"):
        m = re.search(patt, norm_text)
        if m: return int(m.group(1))
    return None


def parse_detail(url: str) -> Review:
    soup = get(url)

    title_el = soup.find("h1")
    title = title_el.get_text(strip=True) if title_el else ""

    # Дата
    date = ""
    t = soup.find("time")
    if t:
        date = t.get_text(strip=True) or ""
        if not re.search(r"\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}", date):
            dt_attr = t.get("datetime") or ""
            m = re.search(r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})", dt_attr)
            if m:
                y, mo, d, hh, mm = m.groups()
                date = f"{d}.{mo}.{y} {hh}:{mm}"

    norm = soup.get_text("\n", strip=True)
    if not date:
        m_date = re.search(r"\b(\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2})\b", norm)
        date = m_date.group(1) if m_date else ""
    date_dt = parse_review_datetime(date)

    # Автор / город (мягко)
    author = None
    location = None
    m_user = re.search(r"\b(user[_\-\d]+)\b", norm)
    if m_user:
        author = m_user.group(1)
        m_loc = re.search(r"(?:^|\s)(г\.\s*[А-ЯЁA-Za-zё\- ]+|[А-ЯЁ][а-яёA-Za-z\- ]+\s*\([^)]+\))", norm)
        if m_loc:
            location = m_loc.group(1).strip()

    rating = extract_rating(soup, norm)
    validation, is_valid = extract_validation(norm)

    # Основной текст
    start_markers = [
        "Отзыв проверяется", "Отзыв проверяется.",
        "Отзыв проверен", "Отзыв проверен.",
        "Документы прикреплены",
        "Проблема решена",
    ]
    end_markers = ["Комментарии", "Ответ банка", "Официальный ответ", "Оставьте отзыв", "Администратор народного рейтинга"]

    start_idx = None
    for sm in start_markers:
        i = norm.find(sm)
        if i != -1:
            start_idx = i + len(sm)
            break

    BANK_HEADER_RE = re.compile(
        r"(?m)^Газпромбанк\s*$"
        r"(?:\r?\n)+"
        r"("
        r"\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}"
        r"|"
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?(?:[+-]\d{2}:\d{2})?"
        r")"
    )
    bank_header = BANK_HEADER_RE.search(norm)

    end_candidates = []
    if start_idx is not None:
        for em in end_markers:
            j = norm.find(em, start_idx)
            if j != -1:
                end_candidates.append(j)
        if bank_header:
            end_candidates.append(bank_header.start())

    end_idx = min(end_candidates) if end_candidates else None

    if start_idx is not None:
        chunk = norm[start_idx:end_idx].strip() if end_idx is not None else norm[start_idx:].strip()
        service_markers = [
            "Документы прикреплены",
            "Отзыв проверяется", "Отзыв проверяется.",
            "Отзыв проверен", "Отзыв проверен.",
            "Проблема решена",
        ]
        changed = True
        while changed:
            changed = False
            for sm in service_markers:
                if chunk.startswith(sm):
                    chunk = chunk[len(sm):].lstrip()
                    changed = True
        lines = [l.strip() for l in chunk.splitlines()]
        lines = [l for l in lines if l and not re.fullmatch(r"[•\-–—]+", l)]
        review_text = "\n\n".join(lines).strip()
    else:
        ps = [p.get_text(" ", strip=True) for p in soup.select("article p, .article p, p")]
        ps = [p for p in ps if len(p) > 40]
        review_text = "\n\n".join(ps) if ps else ""

    # Ответ банка
    bank_response_date = None
    bank_response_text = None
    if bank_header:
        bank_response_date = bank_header.group(1)
        resp_start = bank_header.end()
        resp_end_candidates = []
        for em in ["Комментарии", "Оставьте отзыв", "Администратор народного рейтинга"]:
            j = norm.find(em, resp_start)
            if j != -1:
                resp_end_candidates.append(j)
        resp_end = min(resp_end_candidates) if resp_end_candidates else None
        resp_chunk = norm[resp_start:resp_end].strip() if resp_end is not None else norm[resp_start:].strip()
        rlines = [l.strip() for l in resp_chunk.splitlines()]
        rlines = [l for l in rlines if l and not re.fullmatch(r"[•\-–—]+", l)]
        bank_response_text = "\n\n".join(rlines).strip()

    return Review(
        title=title,
        date=date,
        rating=rating,
        author=author,
        location=location,
        text=review_text,
        url=url,
        bank_response_date=bank_response_date,
        bank_response_text=bank_response_text,
        date_dt=date_dt,
        validation=validation,
        is_valid=is_valid,
    )


def crawl_fixed_pagination(start_url: str,
                           start_page: int = 677,
                           max_pages: int = 1200,
                           delay_sec: float = 2.0,
                           limit: Optional[int] = None,
                           reverse_page_order: bool = False,
                           save_every_n_pages: int = 2,
                           backup_prefix: str = "gazprombank_debitcards2",
                           rotate_backups: bool = True) -> List[Review]:
    """
    Идём по страницам; собираем только в диапазоне дат.
    Досрочно останавливаемся, если встретился отзыв старше DATE_FROM.
    """
    seen_links = set()
    out: List[Review] = []
    prev_url = None
    last_backup_path: Optional[str] = None

    for page_idx in range(start_page, start_page + max_pages):
        current_url = set_page_param(start_url, page_idx)
        print(f"[PAGE] {page_idx}: {current_url}")

        try:
            soup = get(current_url, referer=prev_url)
        except Exception as e:
            print(f"[WARN] Не удалось открыть страницу: {e}")
            break

        links_all = extract_review_links(soup, reverse=reverse_page_order)
        new_links = [u for u in links_all if u not in seen_links]
        print(f"[INFO] Найдено ссылок: всего={len(links_all)}, новых={len(new_links)}")

        # если на странице нет новых ссылок — конец категории
        if not new_links:
            with open(os.path.join(RAW_DIR, f"page_{page_idx}.html"), "w", encoding="utf-8") as f:
                f.write(soup.decode())
            print("[INFO] Пустая страница — сохраняем HTML и завершаем.")
            break

        seen_links.update(new_links)
        for i, link in enumerate(new_links, 1):
            if limit is not None and len(out) >= limit:
                print("[INFO] Достигнут общий лимит записей.")
                return out
            try:
                rev = parse_detail(link)

                # --- ключевая логика дат ---
                if rev.date_dt:
                    if rev.date_dt < DATE_FROM:
                        print(f"  [{i:02}] {rev.date} < {DATE_FROM.date()} — прекращаем парсинг.")
                        return out  # досрочно завершаем обход
                    if rev.date_dt > DATE_TO:
                        print(f"  [{i:02}] {rev.date} > {DATE_TO.date()} — пропускаем.")
                        continue
                else:
                    # если дату распарсить не удалось — пропустим
                    print(f"  [{i:02}] не удалось распарсить дату — пропуск.")
                    continue
                # --------------------------------

                out.append(rev)
                print(f"  [{i:02}] OK: {rev.title} — {rev.date} — rating={rev.rating} — {rev.validation}")
                time.sleep(delay_sec + random.uniform(0.4, 1.1))
            except Exception as e:
                print(f"[WARN] Ошибка парсинга {link}: {e}")

        prev_url = current_url

        # бэкап
        if page_idx % save_every_n_pages == 0 and out:
            parsed = to_parsed(out)
            fname = os.path.join(RAW_DIR, f"{backup_prefix}_page{page_idx}.json")
            if rotate_backups and last_backup_path and os.path.exists(last_backup_path):
                try:
                    os.remove(last_backup_path)
                    print(f"[BACKUP] Удалён предыдущий бэкап: {last_backup_path}")
                except Exception as e:
                    print(f"[BACKUP] Не удалось удалить предыдущий бэкап {last_backup_path}: {e}")
            with open(fname, "w", encoding="utf-8") as f:
                json.dump([asdict(p) for p in parsed], f, ensure_ascii=False, indent=2)
            last_backup_path = fname
            print(f"[BACKUP] Сохранено {len(parsed)} отзывов в {fname}")

    return out


def to_parsed(reviews: List[Review],
              bank_name: str = "gazprombank",
              product_type_override: Optional[str] = None) -> List[ParsedReview]:
    parsed = []
    for idx, r in enumerate(reviews, start=1):
        parsed.append(
            ParsedReview(
                review_id=str(idx),
                review_text=r.text,
                review_date=r.date,
                url=r.url,
                parsed_at=datetime.now().isoformat(),
                bank_name=bank_name,
                product_type=product_type_override or product_type,
                rating=r.rating,
                tonality=tonality_by_rating(r.rating),
                validation=r.validation,
                is_valid=r.is_valid,
            )
        )
    return parsed


def save_csv(items: List[Review], path: str):
    if not items: return
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(asdict(items[0]).keys()))
        w.writeheader()
        for it in items: w.writerow(asdict(it))


def save_json(items: List[Review], path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump([asdict(it) for it in items], f, ensure_ascii=False, indent=2)


def crawl_categories(categories: List[Category],
                     delay_sec: float = 2.5,
                     save_every_n_pages: int = 2,
                     rotate_backups: bool = True) -> List[ParsedReview]:
    all_parsed: List[ParsedReview] = []

    for cat in categories:
        print("\n" + "="*80)
        print(f"[CATEGORY] {cat.product_type} — стартуем: {cat.url} (с {cat.start_page}-й страницы)")
        print("="*80)

        global LIST_URL, product_type
        LIST_URL = cat.url
        product_type = cat.product_type

        backup_prefix = cat.backup_prefix or re.sub(r'[^a-zA-Z0-9_-]+', '_', f"{cat.product_type}")

        reviews = crawl_fixed_pagination(
            start_url=cat.url,
            start_page=cat.start_page,
            max_pages=cat.max_pages,
            delay_sec=delay_sec,
            limit=None,
            reverse_page_order=False,
            save_every_n_pages=save_every_n_pages,
            backup_prefix=backup_prefix,
            rotate_backups=rotate_backups,
        )

        if reviews:
            parsed = to_parsed(reviews, bank_name="gazprombank", product_type_override=cat.product_type)
            all_parsed.extend(parsed)

            out_name = f"{cat.file_name}.json" if cat.file_name else re.sub(
                r'[^a-zA-Z0-9_-]+', '_', f"{cat.product_type}_parsed.json"
            )
            out_path = os.path.join(RAW_DIR, out_name)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump([asdict(p) for p in parsed], f, ensure_ascii=False, indent=2)
            print(f"[DONE] '{cat.product_type}': сохранено {len(parsed)} отзывов в {out_path}")
        else:
            print(f"[DONE] '{cat.product_type}': подходящих отзывов не найдено.")

    return all_parsed


if __name__ == "__main__":
    categories = [
        Category(
            url="https://www.banki.ru/services/responses/bank/gazprombank/product/debitcards/?type=alll",
            product_type="Дебетовые карты",
            start_page=677,
            backup_prefix="gazprombank_debitcards2",
            file_name="debitcards2",  # итоговый файл: debitcards2.json
        ),
    ]

    all_parsed = crawl_categories(categories, delay_sec=2.5, save_every_n_pages=2, rotate_backups=True)

    if all_parsed:
        all_out = os.path.join(RAW_DIR, "all_categories_parsed.json")
        with open(all_out, "w", encoding="utf-8") as f:
            json.dump([asdict(p) for p in all_parsed], f, ensure_ascii=False, indent=2)
        print(f"[TOTAL DONE] Всего сохранено: {len(all_parsed)} отзывов в {all_out}")
    else:
        print("[TOTAL DONE] Отзывов не найдено ни в одной категории.")
