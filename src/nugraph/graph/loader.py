"""Load novels into Neo4j as `:Novel` nodes, and (M2) wire up relationships.

Design notes
------------
- Each novel becomes one `(:Novel {id})` node. `id` is the NovelUpdates series id and is
  the unique key for everything (relations reference these ids).
- genres / tags / authors / assoc_names are stored as **list properties** on the node. That's
  enough for content-similarity (computed in Python) and same-author grouping, and avoids the
  extra complexity of separate Tag/Genre/Author nodes (can be added later for tag-browsing).
- Loads are **batched** with `UNWIND` for speed and are **idempotent** (MERGE on id), so the
  script can be re-run safely.
"""

from __future__ import annotations

from collections.abc import Sequence

from neo4j import Driver

# Scalar properties copied straight onto the node (skipped when null).
SCALAR_KEYS = [
    "name", "novel_type", "cover_url", "original_language", "start_year",
    "original_publisher", "english_publisher", "chapters_original_current",
    "licensed", "complete_original", "complete_translated",
    "rating", "rating_votes", "on_reading_lists", "release_freq",
    "activity_week_rank", "activity_month_rank", "activity_all_time_rank",
    "reading_list_month_rank", "reading_list_all_time_rank",
]
# List-of-string properties.
LIST_KEYS = ["assoc_names", "authors", "genres", "tags"]


def _node_props(rec: dict) -> dict:
    """Build a clean property map for one novel (whitelist + drop nulls)."""
    props: dict = {"id": rec["id"]}
    for k in SCALAR_KEYS:
        v = rec.get(k)
        if v is not None:  # null props are simply omitted in Neo4j
            props[k] = v
    for k in LIST_KEYS:
        v = rec.get(k)
        props[k] = v if isinstance(v, list) else []
    return props


def ensure_constraints(driver: Driver) -> None:
    """Uniqueness constraint on Novel.id (also creates a backing index for fast lookups)."""
    with driver.session() as s:
        s.run("CREATE CONSTRAINT novel_id IF NOT EXISTS FOR (n:Novel) REQUIRE n.id IS UNIQUE")


def load_novels(driver: Driver, records: Sequence[dict], batch_size: int = 1000) -> int:
    """MERGE every record as a :Novel node. Returns the number processed."""
    rows = [_node_props(r) for r in records]
    cypher = """
    UNWIND $rows AS row
    MERGE (n:Novel {id: row.id})
    SET n += row
    """
    with driver.session() as s:
        for i in range(0, len(rows), batch_size):
            s.run(cypher, rows=rows[i : i + batch_size])
    return len(rows)


def novel_count(driver: Driver) -> int:
    with driver.session() as s:
        return s.run("MATCH (n:Novel) RETURN count(n) AS c").single()["c"]
