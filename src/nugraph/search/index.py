"""Qdrant collection: one point per novel, vector = embedding of its synopsis.

Where a synopsis hasn't been scraped yet, we fall back to embedding
`name + genres + tags` so every novel is searchable from day one; the point is simply
re-upserted with the real synopsis once the scrape reaches it (`has_synopsis` flips True).
"""

from __future__ import annotations

from qdrant_client import models

from ..config import settings
from ..db import get_qdrant, shared_qdrant
from ..ingest import synopsis_store as store
from ..ingest.dataset import load_records
from .embed import embed_query, embed_texts


def ensure_collection(client=None, recreate: bool = False):
    client = client or get_qdrant()
    name = settings.qdrant_collection
    if recreate and client.collection_exists(name):
        client.delete_collection(name)
    if not client.collection_exists(name):
        client.create_collection(
            name,
            vectors_config=models.VectorParams(
                size=settings.embedding_dim, distance=models.Distance.COSINE
            ),
        )
    return client


def _text_for(rec: dict, synopses: dict[int, str]) -> tuple[str, bool]:
    """Return (text_to_embed, has_real_synopsis)."""
    desc = synopses.get(rec["id"])
    if desc:
        return desc, True
    parts = [rec.get("name") or ""]
    if rec.get("genres"):
        parts.append("Genres: " + ", ".join(rec["genres"]))
    if rec.get("tags"):
        parts.append("Tags: " + ", ".join(rec["tags"][:30]))
    return ". ".join(p for p in parts if p), False


def build_index(batch: int = 256, recreate: bool = False) -> tuple[int, int]:
    """(Re)build the Qdrant index. Returns (n_points, n_with_synopsis)."""
    client = ensure_collection(recreate=recreate)
    records = load_records()
    synopses = store.get_descriptions()

    ids, texts, payloads = [], [], []
    for rec in records:
        text, has_syn = _text_for(rec, synopses)
        ids.append(rec["id"])
        texts.append(text)
        payloads.append(
            {
                "id": rec["id"],
                "name": rec.get("name"),
                "language": rec.get("original_language"),
                "genres": rec.get("genres") or [],
                "tags": rec.get("tags") or [],
                "rating": rec.get("rating"),
                "novel_type": rec.get("novel_type"),
                "has_synopsis": has_syn,
            }
        )

    vectors = embed_texts(texts, batch_size=batch)
    points = [
        models.PointStruct(id=ids[i], vector=vectors[i].tolist(), payload=payloads[i])
        for i in range(len(ids))
    ]
    for i in range(0, len(points), 1000):
        client.upsert(settings.qdrant_collection, points[i : i + 1000])

    return len(points), sum(p["has_synopsis"] for p in payloads)


def search(query: str, k: int = 10, language: str | None = None, genre: str | None = None) -> list[dict]:
    """Semantic search. Optional payload filters on language / genre."""
    client = shared_qdrant()
    conditions = []
    if language:
        conditions.append(
            models.FieldCondition(key="language", match=models.MatchValue(value=language))
        )
    if genre:
        conditions.append(models.FieldCondition(key="genres", match=models.MatchValue(value=genre)))
    flt = models.Filter(must=conditions) if conditions else None

    res = client.query_points(
        settings.qdrant_collection,
        query=embed_query(query),
        limit=k,
        query_filter=flt,
        with_payload=True,
    ).points
    return [{"id": p.id, "score": round(p.score, 4), **(p.payload or {})} for p in res]
