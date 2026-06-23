"""Local, free sentence embeddings (CPU) used for both semantic search and similarity.

Model is loaded once and cached. We L2-normalize embeddings so cosine == dot product,
matching the Qdrant collection's Cosine distance.
"""

from __future__ import annotations

from collections.abc import Sequence
from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

from ..config import settings


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    return SentenceTransformer(settings.embedding_model)


def embed_texts(texts: Sequence[str], batch_size: int = 256, progress: bool = True) -> np.ndarray:
    model = get_model()
    return model.encode(
        list(texts),
        batch_size=batch_size,
        show_progress_bar=progress,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )


def embed_query(text: str) -> list[float]:
    return embed_texts([text], progress=False)[0].tolist()
