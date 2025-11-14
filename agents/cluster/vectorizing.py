from sklearn.feature_extraction.text import TfidfVectorizer
from pathlib import Path
import json
import os
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import re
import processing


class vectorizer:

    def __init__(self):

        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.vectorizer = TfidfVectorizer(max_features=5000, stop_words="english")

    def get_all_files_in_directory(self, directory: Path, extension: str):

        file_paths = []

        for root, _, files in os.walk(directory):

            for file in files:

                if file.endswith(f".{extension}"):

                    file_paths.append(Path(root) / file)

        return file_paths

    def load_articales(
        self,
        # default to repository-level data/db (agents/cluster -> .. (agents) -> .. (repo root))
        path=Path(__file__).parent.parent.parent / "data" / "db",
        format="json",
        structure="by_date",
        use_json=True,
        index="index.json",
    ):

        self.root_db_path = path
        self.format = format
        self.structure = structure
        self.use_json = use_json
        self.index = index
        self.index_file = self.root_db_path / self.index
        self.articales_dir = self.root_db_path / self.structure

        # load all articles from the db

        all_articales = []
        all_files = self.get_all_files_in_directory(
            self.articales_dir, extension=self.format
        )

        for file_path in all_files:

            with open(file_path, "r", encoding="utf-8") as f:

                try:

                    data = json.load(f)

                    for artacle in data:

                        all_articales.append(artacle)

                except Exception as e:

                    print(f"Error loading {file_path}: {e}")

        self.articales = all_articales

    def prepare_texts(self, articles="use_loaded"):

        if articles == "use_loaded":

            articles = self.articales

        texts = {}

        for article in articles:

            title = article.get("title", "")

            text = article.get("text", "")
            processer = processing.TextProcessor(text)
            clean_text = processer.clean_text()

            id = article.get("id", "")

            texts[id] = f"{title} \n {clean_text}"
        return texts
    
    def order_articles_by_id(self):

        if not hasattr(self, "articales"):
            raise ValueError("Articles not loaded. Please run load_articales() first.")

        articles_by_id = {}
        for article in self.articales:
            id = article.get("id", "")
            articles_by_id[id] = article

        return articles_by_id

    def vectorize_texts(self):

        texts_by_id = self.prepare_texts()
        self.articles_by_id = self.order_articles_by_id()
        ids = list(texts_by_id.keys())

        sentences = [texts_by_id[i] for i in ids]

        # If there are no texts, return empty arrays shaped for the model
        if not sentences:
            dim = getattr(self.model, "get_sentence_embedding_dimension", lambda: 0)()
            # fallback to 0-dim if model doesn't expose dimension
            if not dim:
                X = np.empty((0, 0))
            else:
                X = np.empty((0, dim))

            embeddings_by_id = {}
            return X, embeddings_by_id

        X = self.model.encode(sentences, normalize_embeddings=True)

        embeddings_by_id = {i: X[idx] for idx, i in enumerate(ids)}

        return X, embeddings_by_id


if __name__ == "__main__":

    vec = vectorizer()
    vec.load_articales()

    vec.vectorize_texts()
