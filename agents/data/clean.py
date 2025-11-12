import importlib.util
from pathlib import Path
import hashlib, time, re, os
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
import datetime as dt
from dateutil import parser as dateparser

ROOT_DIR = Path(__file__).parent.parent.parent
LIB_DIR = ROOT_DIR / "data" / "agents"
LIB_NAME = "process_yml"


"""
print(f"ROOT_DIR: {ROOT_DIR}")
print(f"LIB_DIR: {LIB_DIR}")
print(f"LIB_NAME: {LIB_NAME}")
print(f"ALL TOGETHER: {LIB_DIR / LIB_NAME}")
"""

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

    def sanitize_text(self, text: str) -> str:

        if not text:

            return ""

        text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]+", " ", text)

        # get rid of things that are common but not useful to the interpretation of the artacle

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

        # More lenient threshold since we're looking at sentences
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

            # validate presence
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

    cleaned_articles = cleaner_instance.process_articles(raw_articles)

    with open("cleaned_articles.json", "w", encoding="utf-8") as f:

        import json

        json.dump({"articles": cleaned_articles}, f, ensure_ascii=False, indent=4)
