import from_yml
import fetch


class processer:

    def __init__(self):

        self.data = from_yml.load_feeds()
        self.fetcher = fetch.fetcher()

    def example_archetecture(self):

        return {
            {
                "defaults": {
                    "request": {
                        "timeout_sec": 8,
                        "headers": {"User-Agent": "SpaceRadar/1.0"},
                    },
                    "parse": {"prefer_fulltext": True, "max_items_per_feed": 50},
                },
                "sources": [
                    {
                        "name": "NASA",
                        "url": "https://www.nasa.gov/news-release/feed/",
                        "topics": ["earthobs", "missions"],
                    },
                    {
                        "name": "NASA Blogs",
                        "url": "https://blogs.nasa.gov/feed/",
                        "topics": ["missions"],
                    },
                ],
                "selectors": {
                    "SpaceNews": {
                        "article": "article",
                        "content": "article .post-content p",
                    },
                    "Spaceflight Now": {
                        "article": "article",
                        "content": "article .entry-content p",
                    },
                },
            }
        }

    def list_sources(self):

        return [source["name"] for source in self.data.get("sources", [])]

    def get_source_info(self, name: str):

        return self.data.get("sources", {})

    def yeild_sources_info(self):

        for source in self.data.get("sources", []):

            yield source

    def fetch_sources_raw(self):

        sources_raw = []

        for source in self.yeild_sources_info():

            feed_url = source.get("url", "")

            if not feed_url:
                continue

            articles = self.fetcher.pull(feed_url)

            sources_raw.append(
                {
                    "source": source.get("name", "Unknown"),
                    "url": feed_url,
                    "articles": articles,
                }
            )

        return sources_raw
    
    def get_articales(self, raw_data=None):

        if raw_data is None:


if __name__ == "__main__":

    proc = processer()

    with open("example.json", "w", encoding="utf-8") as f:

        print("Writing example.json...")

        import json

        print("Fetched sources:", proc.list_sources())

        json.dump(proc.fetch_sources_raw(), f, indent=2, ensure_ascii=False)

        print("Done.")
