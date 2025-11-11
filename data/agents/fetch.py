import feedparser
import requests
from typing import List, Dict, Any
from dateutil import parser as dtp
from bs4 import BeautifulSoup


class fetcher:

    def __init__(self):
        self.feed_urls = []
        self.feed_config = {}

    def timestamp_to_iso(self, ts: str) -> str:
        try:
            dt = dtp.parse(ts)
            return dt.isoformat()
        except Exception:
            return ""

    def set_urls(self, urls: List[str]) -> None:
        self.feed_urls = urls

    def set_config(self, feed_config: Dict[str, Any]) -> None:
        self.feed_config = feed_config

    def pull(
        self, feed_url: str, max_items: int = 50, timeout: int = 8
    ) -> List[Dict[str, Any]]:
        max_items = self.feed_config.get("max_items_per_feed", max_items)
        timeout = self.feed_config.get("request", {}).get("timeout_sec", timeout)

        feed = feedparser.parse(feed_url)
        outputs: List[Dict[str, Any]] = []

        for entry in feed.entries[:max_items]:
            url = entry.get("link", "")
            title = entry.get("title", "No Title").strip()
            ts = self.timestamp_to_iso(
                entry.get("published", None) or entry.get("updated", "")
            )

            text = ""

            if "content" in entry and len(entry.content) > 0:
                text = " ".join(
                    BeautifulSoup(c.value, "html.parser").get_text(" ", strip=True)
                    for c in entry.content
                )[:10000]
            else:
                text = (entry.get("summary") or "").strip()

                if len(text) < 200 and url:
                    try:
                        r = requests.get(url, timeout=timeout)
                        r.raise_for_status()

                        soup = BeautifulSoup(r.text, "html.parser")
                        text = " ".join(
                            p.get_text(" ", strip=True) for p in soup.find_all("p")
                        )[:10000]
                    except Exception:
                        pass

            outputs.append({"url": url, "title": title, "ts": ts, "text": text})

        return outputs

    def in_lists(self) -> List[Dict[str, Any]]:
        all_items: List[Dict[str, Any]] = []

        for feed_url in self.feed_urls:
            items = self.pull(feed_url)
            all_items.extend(items)

        return all_items
