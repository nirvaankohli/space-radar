import importlib.util
from pathlib import Path
import hashlib, time, re, os
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
import datetime as dt
from dateutil import parser as dateparser
import json
import datetime

ROOT_DIR = Path(__file__).parent.parent.parent
LIB_DIR = ROOT_DIR / "data" / "agents"
LIB_NAME = "process_yml"

spec = importlib.util.spec_from_file_location(LIB_NAME, LIB_DIR / f"{LIB_NAME}.py")
process_yml = importlib.util.module_from_spec(spec)
spec.loader.exec_module(process_yml)

proc = process_yml.processer()


class cleaner:

    def __init__(self):

        pass

    def make_id(self, url: str, title: str) -> str:

        hash_input = (url + title).encode("utf-8")
        return hashlib.md5(hash_input).hexdigest()

    def normalize_articles(self, articles=None):

        if articles is None:
            articles = proc.get_articales()

        cleaned_articles = []

        for article in articles:

            text = article.get("text", "").strip()

            if not text:
                continue

            cleaned_article = {
                "id": self.make_id(
                    article.get("article_url", ""), article.get("title", "")
                ),
                "source": article.get("source", "Unknown").strip(),
                "url": article.get("article_url", "").strip(),
                "title": article.get("title", "").strip(),
                "timestamp": article.get("timestamp", "").strip(),
                "text": text,
            }

            cleaned_articles.append(cleaned_article)

        return cleaned_articles

    def canonical_url(self, url: str) -> str:

        if not url:
            return ""
        try:
            p = urlparse(url)
            qs = [
                (k, v)
                for k, v in parse_qsl(p.query, keep_blank_values=True)
                if k.lower()
                not in {
                    "utm_source",
                    "utm_medium",
                    "utm_campaign",
                    "utm_term",
                    "utm_content",
                    "fbclid",
                    "gclid",
                }
            ]
            p = p._replace(query=urlencode(qs, doseq=True), fragment="")
            p = p._replace(netloc=p.netloc.lower())
            return urlunparse(p)
        except Exception:
            return url

    def clean_title(self, t: str) -> str:

        if not t:

            return ""

        s = t.strip()
        s = re.sub(r"^[\'\"]+|[\'\"]+$", "", s)
        s = re.sub(
            r"\s*[-–—:]\s*(NASA|JPL|ESA|SpaceNews|Spaceflight Now|Planetary Society|Nature|arXiv)\b$",
            "",
            s,
            flags=re.IGNORECASE,
        )

        s = re.sub(r"\s+", " ", s)

        return s

    def parse_ts(self, ts_raw):

        if not ts_raw:

            return None

        try:

            dtv = dateparser.parse(ts_raw)

            if dtv is None:

                return None

            if dtv.tzinfo is None:

                dtv = dtv.replace(tzinfo=dt.timezone.utc)

            return dtv.astimezone(dt.timezone.utc).isoformat()

        except Exception:

            return None

    def get_rid_of_img_tags(self, text: str) -> str:

        if not text:
            return ""

        text = re.sub(r"<img[^>]*>", "", text, flags=re.IGNORECASE)

        return text

    def sanitize_text(self, text: str) -> str:

        if not text:
            return ""

        text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]+", " ", text)
        text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
        text = self.get_rid_of_img_tags(text)
        try:
            import processing as _processing
        except Exception:
            try:
                spec_proc = importlib.util.spec_from_file_location(
                    "processing", Path(__file__).parent / "processing.py"
                )
                _processing = importlib.util.module_from_spec(spec_proc)
                spec_proc.loader.exec_module(_processing)
            except Exception:
                _processing = None

        if _processing is not None:
            try:
                proc = _processing.TextProcessor(text)
                cleaned = proc.clean_text()
                if cleaned:
                    text = cleaned
            except Exception:
                pass

        cut_patterns = [
            r"Credits?:",
            r"Contact:",
            r"Subscribe",
            r"Sign in to",
            r"All rights reserved",
            r"Read more",
            r"TL;DR",
            r"Follow us on",
            r"Socials",
        ]

        for pat in cut_patterns:
            idx = text.lower().rfind(pat.lower())
            if idx != -1 and idx > len(text) - 800:
                text = text[:idx]
                break

        text = re.sub(r"\s+", " ", text).strip()

        if len(text) > 10000:
            text = text[:10000]

        return text

    def is_boilerplate(self, text: str) -> bool:

        if not text or len(text.strip()) < 100:
            return True

        # Split on sentences rather than lines since sanitize_text removes newlines
        import re

        sentences = [
            s.strip()
            for s in re.split(r"[.!?]+", text)
            if s.strip() and len(s.strip()) > 10
        ]

        if not sentences or len(sentences) < 3:
            return True

        from collections import Counter

        c = Counter(sentences)

        most = c.most_common(1)[0][1] if sentences else 0

        if most / max(1, len(sentences)) > 0.6:
            return True

        markers = [
            "share details",
            "-end-",
            "click here",
            "continue reading",
            "read more",
            "subscribe",
            "follow us",
        ]

        text_lower = text.lower()

        for marker in markers:

            if marker in text_lower:

                return True
        return False

    def process_articles(self, articles=None):

        if articles is None:
            articles = proc.get_articales()

        first_pass = self.normalize_articles(articles)

        outputs = []
        now_iso = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc).isoformat()

        source_map = {
            "nasa.gov": "NASA",
            "jpl.nasa.gov": "JPL",
            "esa.int": "ESA",
            "spacenews.com": "SpaceNews",
            "spaceflightnow.com": "SpaceflightNow",
            "arxiv.org": "arXiv",
        }

        for a in first_pass:
            url = a.get("url") or a.get("article_url") or ""
            title = a.get("title") or ""
            source = a.get("source") or ""
            ts_raw = a.get("timestamp") or a.get("ts") or ""
            text = a.get("text") or ""

            url_c = self.canonical_url(url)
            title_c = self.clean_title(title)
            ts_c = self.parse_ts(ts_raw)
            text_s = self.sanitize_text(text)

            if not title_c:
                continue
            if len(title_c) < 12:
                continue
            if len(text_s) < 200:
                continue
            if self.is_boilerplate(text_s):
                continue

            if not ts_c:

                ts_try = a.get("fetch_ts") or a.get("fetched_at")

                if ts_try:

                    ts_c = self.parse_ts(ts_try)

            if not ts_c:

                continue

            try:

                host = urlparse(url_c).netloc.lower()
            except Exception:

                host = ""

            src_canon = source_map.get(host, source or host)

            cleaned = {
                "id": self.make_id(url_c, title_c),
                "url": url_c,
                "source": src_canon,
                "title": title_c,
                "timestamp": ts_c,
                "text": text_s,
                "text_len": len(text_s),
            }

            outputs.append(cleaned)

        return outputs


if __name__ == "__main__":

    cleaner_instance = cleaner()

    try:

        raw_articles = proc.get_articales()

    except Exception as e:

        print(f"Failed to fetch articles, using example data: {e}")

        import json

        with open(
            ROOT_DIR / "data" / "agents" / "example.json", "r", encoding="utf-8"
        ) as f:

            example_data = json.load(f)

        raw_articles = []

        for source in example_data:

            for article in source.get("articles", []):

                raw_articles.append(
                    {
                        "source": source.get("source", "Unknown"),
                        "source_url": source.get("url", ""),
                        "article_url": article.get("url", ""),
                        "title": article.get("title", ""),
                        "timestamp": article.get("ts", ""),
                        "text": article.get("text", ""),
                    }
                )

    # get articles

    cleaned_articles = cleaner_instance.process_articles(raw_articles)

    # set up/init paths

    db_path = ROOT_DIR / "data" / "db"
    db_path.mkdir(parents=True, exist_ok=True)
    index_file = db_path / "index.json"

    # load existing index data

    try:

        # read & create if not exist

        if index_file.exists():

            with open(index_file, "r", encoding="utf-8") as f:

                og_data = json.load(f) or {}

        else:

            og_data = {}
    except Exception:

        og_data = {}

    # key for ids

    if "id" in og_data and isinstance(og_data["id"], list):
        key = "id"
    elif "ids" in og_data and isinstance(og_data["ids"], list):
        key = "ids"
    else:
        key = "id"

    og_data.setdefault(key, [])

    existing_ids_before = set(og_data.get(key, []))

    if not index_file.exists():
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(og_data, f, ensure_ascii=False, indent=2)

    # find new articles (not in original index)
    new_articles = []
    new_ids = []

    for article in cleaned_articles:
        if article["id"] not in existing_ids_before:
            new_articles.append(article)
            new_ids.append(article["id"])

    # only proceed if there are new articles

    if new_articles:

        # update index with new IDs

        updated_data = og_data.copy()
        updated_data.setdefault(key, [])
        if not isinstance(updated_data[key], list):
            updated_data[key] = (
                list(updated_data[key]) if updated_data[key] is not None else []
            )

        updated_data[key].extend(new_ids)

        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(updated_data, f, ensure_ascii=False, indent=2)

        # add new articles to date-based file

        date_folder_path = db_path / "by_date"
        date_folder_path.mkdir(parents=True, exist_ok=True)

        today_date = datetime.datetime.utcnow().strftime("%Y-%m-%d")
        date_path = date_folder_path / f"{today_date}.json"

        # load existing date file or create empty list

        try:

            if date_path.exists():

                with open(date_path, "r", encoding="utf-8") as f:

                    existing_date_data = json.load(f)

            else:

                existing_date_data = []

        except Exception:

            existing_date_data = []

        # add new articles to date file

        existing_date_data.extend(new_articles)

        with open(date_path, "w", encoding="utf-8") as f:

            json.dump(existing_date_data, f, ensure_ascii=False, indent=2)

        print(f"Added {len(new_articles)} new articles to {today_date}.json")

    else:

        print("No new articles to add")

    output_file = ROOT_DIR / "cleaned_articles.json"

    with open(output_file, "w", encoding="utf-8") as f:

        json.dump({"articles": cleaned_articles}, f, ensure_ascii=False, indent=2)

    print(f"Total cleaned articles: {len(cleaned_articles)}")
    print(f"New articles added: {len(new_articles)}")
    print(f"Output saved to: {output_file}")
