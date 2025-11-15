import clustering


class processing:

    def __init__(self, threshold=0.7):

        cluster_agent = clustering.ClusteringAgent()
        cluster_agent.fit_clusters()
        cluster_agent.build_clusters(threshold=threshold)
        self.clusters = cluster_agent.clusters_to_ids()
        self.articles_by_id = cluster_agent.articles_by_id

    def construct(self):

        story_candidates = []

        for cluster in self.clusters:

            rep = self.articles_by_id[cluster.get("rep_id", "")]
            cluster_attr = []

            for i in cluster.get("member_ids", []):

                article = self.articles_by_id[i]

                cluster_attr.append(
                    {
                        "id": i,
                        "title": article.get("title", ""),
                        "source": article.get("source", ""),
                        "url": article.get("url", ""),
                        "text": article.get("text", ""),
                        "timestamp": article.get("timestamp", ""),
                    }
                )

            candidate = {
                "cluster_id": cluster.get("cluster_id", ""),
                "rep_id": cluster.get("rep_id", ""),
                "member_ids": cluster.get("member_ids", []),
                "rep_title": rep.get("title", ""),
                "sources": [i.get("source", "") for i in cluster_attr],
                "timestamp": rep.get("timestamp", ""),
                "articles": cluster_attr,
                "urls": [i.get("url", "") for i in cluster_attr],
                "rep_text": rep.get("text", ""),
                "summary": "",
                "topics": [""],
                "because": "",
                "score": 0.0,
                "score_components": {},
            }

            story_candidates.append(candidate)

        self.story_candidates = story_candidates

        return self.story_candidates, self.articles_by_id


if __name__ == "__main__":

    import time
    from pathlib import Path

    db_dir = Path(__file__).parent.parent.parent / "data" / "db"

    start_time = time.time()

    proc = processing(threshold=0.7)
    i, art = proc.construct()
    with open(db_dir / "story_candidates.json", "w", encoding="utf-8") as f:

        import json

        json.dump(i, f, ensure_ascii=False, indent=4)

    end_time = time.time()
    print(f"Processing time: {end_time - start_time} seconds")
