from sklearn.neighbors import NearestNeighbors
import numpy as np
from pathlib import Path

ROOT_DIR = Path(__file__).parent

import vectorizing


class ClusteringAgent:

    def __init__(self, k=5):

        self.vec = vectorizing.vectorizer()
        self.vec.load_articales()
        self.X, self.embeddings_by_id = self.vec.vectorize_texts()
        self.k = k

    def choose_k(self):

        # elbow method to choose k
        Ks = range(3, 17)
        self.k = 5  # placeholder for chosen k

    def fit_clusters(self):

        nn = NearestNeighbors(n_neighbors=min(self.k, len(self.X)), metric="cosine")
        nn.fit(self.X)

        self.nn = nn

    def build_clusters(self, threshold=0.88):

        self.articles_by_id = self.vec.order_articles_by_id()
        self.by_id = self.vec.prepare_texts()

        self.ids = list(self.by_id.keys())
        seen = set()
        clusters_idx = []

        for i in range(len(self.ids)):

            if i in seen:

                continue

            distances, indices = self.nn.kneighbors(
                self.X[i].reshape(1, -1), return_distance=True
            )
            distances = distances[0]
            indices = indices[0]

            group = []

            for j, d in zip(indices, distances):

                sim = 1.0 - d

                if sim >= threshold:

                    group.append([j, sim])

            for j, sim in group:

                seen.add(j)

            clusters_idx.append(group)

        self.clusters_idx = clusters_idx

    def clusters_to_ids(self):

        clusters = []
        for group in self.clusters_idx:

            member_ids = [self.ids[j] for j, _ in group]
            rep_id = member_ids[0]
            clusters.append(
                {
                    "cluster_id": rep_id,
                    "member_ids": member_ids,
                    "rep_id": rep_id,
                    "sim": [sim for _, sim in group],
                }
            )

        return clusters


if __name__ == "__main__":

    import time

    start_time = time.time()

    cluster_agent = ClusteringAgent()
    cluster_agent.fit_clusters()
    cluster_agent.build_clusters(threshold=0.7)
    clusters = cluster_agent.clusters_to_ids()
    end_time = time.time()

    f = cluster_agent.by_id
    p = []

    print(clusters[0])

    for cluster in clusters:

        if len(cluster["member_ids"]) > 1:

            rep_id = cluster.get("rep_id")
            rep_text = f.get(rep_id, "")

            l = []

            for idx, mid in enumerate(cluster["member_ids"]):
                sim = None
                try:

                    sim = cluster["sim"][idx]

                    try:
                        sim = float(sim)
                    except Exception:
                        sim = None
                except Exception:
                    sim = None

                member_text = f.get(mid, "")

                l.append(
                    {
                        "id": mid,
                        "sim": sim,
                        "text": str(member_text),
                        "rep_text": str(rep_text),
                    }
                )

            p.append(l)

    with open("sample_clusters.json", "w", encoding="utf-8") as f:

        import json

        json.dump(p, f, indent=2)

    print(
        f"Total clusters formed: {len(clusters)} out of {len(cluster_agent.ids)} articles"
    )
    print(f"Clustering took {end_time - start_time:.2f} seconds")
    print(cluster_agent.X.shape)
    print(cluster_agent.X.dtype)
    print(np.linalg.norm(cluster_agent.X[0]))
    print(np.mean([np.linalg.norm(v) for v in cluster_agent.X]))
