import os
import json
import numpy as np
from typing import List, Dict, Any


class LocalVectorDB:
    def __init__(self, dim: int = 384, db_dir: str = "vector_db_store"):
        self.dim = dim
        self.db_dir = db_dir

        self.vec_path = os.path.join(db_dir, "vectors.npy")
        self.meta_path = os.path.join(db_dir, "metadata.json")

        os.makedirs(db_dir, exist_ok=True)

        self._load()

    # ----------------------------------------------------------
    # Internal
    # ----------------------------------------------------------

    def _load(self):
        """Load vectors + metadata if available."""
        if os.path.exists(self.vec_path) and os.path.exists(self.meta_path):
            self.vectors = np.load(self.vec_path)
            with open(self.meta_path, "r") as f:
                meta = json.load(f)
                self.ids = meta["ids"]
                self.payloads = meta["payloads"]
        else:
            self.vectors = np.zeros((0, self.dim), dtype=np.float32)
            self.ids = []
            self.payloads = {}

    def _save(self):
        np.save(self.vec_path, self.vectors)
        with open(self.meta_path, "w") as f:
            json.dump({
                "ids": self.ids,
                "payloads": self.payloads
            }, f)

    # ----------------------------------------------------------
    # Public API
    # ----------------------------------------------------------

    def upsert_documents(self, ids: List[str], embeddings: List[List[float]], metadatas: List[Dict[str, Any]]):
        new_vectors = np.array(embeddings, dtype=np.float32)

        # Append to existing database
        self.vectors = np.vstack([self.vectors, new_vectors])

        for i, doc_id in enumerate(ids):
            self.ids.append(doc_id)
            self.payloads[doc_id] = metadatas[i]

        self._save()

    def search_vector(self, query_vector: List[float], top_k: int = 5):
        if len(self.vectors) == 0:
            return []

        q = np.array(query_vector, dtype=np.float32).reshape(1, -1)

        # Cosine similarity = 1 - cosine distance
        dot_products = np.dot(self.vectors, q.T).reshape(-1)
        norms = (np.linalg.norm(self.vectors, axis=1) * np.linalg.norm(q))
        similarities = dot_products / norms

        # Sort top-k
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            results.append({
                "id": self.ids[idx],
                "score": float(similarities[idx]),
                "payload": self.payloads.get(self.ids[idx], {})
            })

        return results

    def delete(self, ids: List[str]):
        indices_to_keep = [
            i for i, doc_id in enumerate(self.ids)
            if doc_id not in ids
        ]

        self.vectors = self.vectors[indices_to_keep]
        self.ids = [self.ids[i] for i in indices_to_keep]
        self.payloads = {doc_id: self.payloads[doc_id] for doc_id in self.ids}

        self._save()

    def delete_all(self):
        self.vectors = np.zeros((0, self.dim), dtype=np.float32)
        self.ids = []
        self.payloads = {}
        self._save()