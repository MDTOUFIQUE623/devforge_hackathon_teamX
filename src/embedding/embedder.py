"""
Embedding module for converting text blocks into dense vector embeddings.
Using open-source model: sentence-transformers/all-MiniLM-L6-V2
"""

from typing import List
from sentence_transformers import SentenceTransformer


class Embedder:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-V2"):
        """
        Initialize the embedding model.
        Loads the model into memory once for reuse.
        """
        self.model = SentenceTransformer(model_name)

    def encode_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Convert a list of text blocks into embeddings.

        Args:
            texts (List[str]): Multiple text blocks.

        Returns:
            List[List[float]]: Embedding vectors for each text block.
        """
        if not texts:
            raise ValueError("Input text list cannot be empty")

        return self.model.encode(texts, convert_to_numpy=True).tolist()

    def encode_text(self, text: str) -> List[float]:
        """
        Convert a single text block into embedding.

        Args:
            text (str): Input text to embed.

        Returns:
            List[float]: Embedding vector.
        """
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty")

        return self.model.encode([text], convert_to_numpy=True)[0].tolist()
