"""NUgraph API — read-only search + graph endpoints over Neo4j + Qdrant.

    uv run uvicorn nugraph.api.main:app --reload --port 8000

Endpoints
  GET /api/health
  GET /api/facets                         -> {languages, genres} for UI filters
  GET /api/search?q=&k=&language=&genre=  -> semantic "search by description"
  GET /api/novel/{id}                     -> full novel detail (+ synopsis if scraped)
  GET /api/graph/neighbors/{id}?edge_types=&limit=  -> ego-subgraph for the frontend
"""

from __future__ import annotations

from collections import Counter
from contextlib import asynccontextmanager
from functools import lru_cache

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from ..graph import queries
from ..ingest import synopsis_store as store
from ..ingest.dataset import load_records
from ..search.embed import get_model
from ..search.index import search as semantic_search

EDGE_TYPES = ["RELATED", "RECOMMENDS", "SAME_AUTHOR", "CO_LISTED", "SIMILAR"]


@lru_cache(maxsize=1)
def _facets() -> dict:
    recs = load_records()
    languages = sorted({r["original_language"] for r in recs if r.get("original_language")})
    genres = Counter(g for r in recs for g in (r.get("genres") or []))
    return {"languages": languages, "genres": [g for g, _ in genres.most_common(40)]}


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_model()          # warm the embedding model so the first search is fast
    queries.get_novel(5)  # warm the Neo4j connection pool
    _facets()            # precompute filter facets
    yield


app = FastAPI(title="NUgraph API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev: allow the Vite dev server
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/facets")
def facets() -> dict:
    return _facets()


@app.get("/api/search")
def search(
    q: str = Query(..., min_length=1, description="natural-language description"),
    k: int = Query(12, ge=1, le=50),
    language: str | None = None,
    genre: str | None = None,
) -> dict:
    return {"query": q, "results": semantic_search(q, k=k, language=language, genre=genre)}


@app.get("/api/novel/{novel_id}")
def novel(novel_id: int) -> dict:
    n = queries.get_novel(novel_id)
    if n is None:
        raise HTTPException(status_code=404, detail="novel not found")
    n["synopsis"] = store.get_one(novel_id)
    return n


@app.get("/api/graph/neighbors/{novel_id}")
def neighbors(
    novel_id: int,
    edge_types: str = Query(",".join(EDGE_TYPES), description="comma-separated edge types"),
    limit: int = Query(40, ge=1, le=200),
) -> dict:
    center = queries.get_novel(novel_id)
    if center is None:
        raise HTTPException(status_code=404, detail="novel not found")

    wanted = [t for t in edge_types.split(",") if t in EDGE_TYPES]
    rows = queries.get_neighbors(novel_id, wanted, limit)

    # assemble a Cytoscape-friendly payload (unique nodes + edges)
    nodes: dict[int, dict] = {
        center["id"]: {
            "id": center["id"],
            "name": center.get("name"),
            "language": center.get("original_language"),
            "rating": center.get("rating"),
            "center": True,
        }
    }
    edges = []
    for r in rows:
        m = r["neighbor"]
        nodes.setdefault(
            m["id"],
            {
                "id": m["id"],
                "name": m.get("name"),
                "language": m.get("original_language"),
                "rating": m.get("rating"),
                "center": False,
            },
        )
        edges.append(
            {
                "source": r["source"],
                "target": r["target"],
                "type": r["rel"],
                "weight": r["weight"] if r["weight"] is not None else 1.0,
            }
        )
    return {"center": novel_id, "nodes": list(nodes.values()), "edges": edges}
