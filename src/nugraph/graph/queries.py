"""Read-only Neo4j queries used by the API. Keeps Cypher out of the route handlers."""

from __future__ import annotations

from collections.abc import Sequence

from ..db import shared_driver


def get_novel(novel_id: int) -> dict | None:
    """All stored properties of one novel (or None)."""
    with shared_driver().session() as s:
        rec = s.run("MATCH (n:Novel {id:$id}) RETURN n{.*} AS n", id=novel_id).single()
        return rec["n"] if rec else None


def get_neighbors(novel_id: int, types: Sequence[str], limit: int) -> list[dict]:
    """Up to `limit` strongest neighbours of a novel across the given edge types.

    Returns one row per edge: {rel, weight, source, target, neighbor{...}}.
    """
    cypher = """
    MATCH (n:Novel {id:$id})
    CALL { WITH n
        MATCH (n)-[r]-(m:Novel) WHERE type(r) IN $types
        RETURN r, m ORDER BY coalesce(r.weight, 1.0) DESC LIMIT $limit
    }
    RETURN type(r) AS rel, r.weight AS weight,
           startNode(r).id AS source, endNode(r).id AS target,
           m{.id, .name, .original_language, .rating, .novel_type} AS neighbor
    """
    with shared_driver().session() as s:
        return [r.data() for r in s.run(cypher, id=novel_id, types=list(types), limit=limit)]


def search_by_name(term: str, limit: int = 10) -> list[dict]:
    """Simple case-insensitive name lookup (handy for jumping into the graph)."""
    cypher = """
    MATCH (n:Novel)
    WHERE toLower(n.name) CONTAINS toLower($term)
    RETURN n{.id, .name, .original_language, .rating} AS n
    ORDER BY n.rating DESC LIMIT $limit
    """
    with shared_driver().session() as s:
        return [r["n"] for r in s.run(cypher, term=term, limit=limit)]
