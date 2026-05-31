from __future__ import annotations

from typing import Optional

from sentence_transformers import SentenceTransformer


class OpticalEmbedder:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", device: str = "cpu"):
        self._model_name = model_name
        self._device = device
        self._model: Optional[SentenceTransformer] = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self._model_name, device=self._device)
        return self._model

    def encode(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        embeddings = self.model.encode(texts, batch_size=batch_size, show_progress_bar=False)
        return embeddings.tolist()

    def encode_query(self, text: str) -> list[float]:
        return self.model.encode(text, show_progress_bar=False).tolist()

    @property
    def vector_size(self) -> int:
        return self.model.get_sentence_embedding_dimension() or 384
