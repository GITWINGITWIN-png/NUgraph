"""M2: build the relationship edges between :Novel nodes.

Five edge types, each from a different signal:

  (a)-[:RELATED]->(b)       same franchise (sequels/spin-offs), from related_series_ids
  (a)-[:RECOMMENDS]->(b)    user recommendation, from recommended_series_ids
  (a)-[:SAME_AUTHOR]-(b)    share >=1 author        (weight = #shared authors)
  (a)-[:CO_LISTED]-(b)      co-occur in rec-lists   (weight = #shared lists)
  (a)-[:SIMILAR]-(b)        similar tags/genres     (weight = cosine TF-IDF score)

Directed signals (RELATED, RECOMMENDS) are stored as-is. Symmetric signals
(SAME_AUTHOR, CO_LISTED, SIMILAR) are stored once per pair (a.id < b.id) with a
`weight`, and queried undirected.

Anti-hairball measures: cap how many novels a single author/list may connect, require a
minimum amount of sharing, and keep only the top-k strongest neighbours per novel.
"""

from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from collections.abc import Sequence

import numpy as np
from neo4j import Driver

from ..config import settings

# --- tuning knobs (kept here, next to the code that uses them) ---
SAME_AUTHOR_MAX_GROUP = 60   # ignore an author credited on more novels than this (placeholders)
CO_LISTED_MAX_LIST = 40      # ignore rec-lists bigger than this (they connect everything)
CO_LISTED_TOP_K = 15         # keep only each novel's strongest co-listed neighbours


# --------------------------------------------------------------------------- #
# generic loaders
# --------------------------------------------------------------------------- #
def _load_directed(driver: Driver, pairs: Sequence[tuple[int, int]], rel: str, batch: int = 5000) -> int:
    """Create (a)-[:REL]->(b) for each (a,b); both nodes must already exist (dangling ids skipped)."""
    cypher = f"""
    UNWIND $rows AS row
    MATCH (a:Novel {{id: row.a}})
    MATCH (b:Novel {{id: row.b}})
    MERGE (a)-[:{rel}]->(b)
    """
    with driver.session() as s:
        for i in range(0, len(pairs), batch):
            rows = [{"a": a, "b": b} for a, b in pairs[i : i + batch]]
            s.run(cypher, rows=rows)
    return len(pairs)


def _load_weighted(driver: Driver, triples: Sequence[tuple[int, int, float]], rel: str, batch: int = 5000) -> int:
    """Create undirected (a)-[:REL {weight}]-(b); MERGE dedupes regardless of stored direction."""
    cypher = f"""
    UNWIND $rows AS row
    MATCH (a:Novel {{id: row.a}})
    MATCH (b:Novel {{id: row.b}})
    MERGE (a)-[r:{rel}]-(b)
    SET r.weight = row.w
    """
    with driver.session() as s:
        for i in range(0, len(triples), batch):
            rows = [{"a": a, "b": b, "w": w} for a, b, w in triples[i : i + batch]]
            s.run(cypher, rows=rows)
    return len(triples)


# --------------------------------------------------------------------------- #
# edge builders
# --------------------------------------------------------------------------- #
def build_related(driver: Driver, records: Sequence[dict]) -> int:
    pairs = [(r["id"], t) for r in records for t in (r.get("related_series_ids") or [])]
    return _load_directed(driver, pairs, "RELATED")


def build_recommends(driver: Driver, records: Sequence[dict]) -> int:
    pairs = [(r["id"], t) for r in records for t in (r.get("recommended_series_ids") or [])]
    return _load_directed(driver, pairs, "RECOMMENDS")


def _group_pairs(group_to_ids: dict, max_group: int) -> dict[tuple[int, int], int]:
    """Turn {group -> {novel ids}} into {(a,b): #shared groups}, skipping oversized groups."""
    counts: dict[tuple[int, int], int] = defaultdict(int)
    for ids in group_to_ids.values():
        if 2 <= len(ids) <= max_group:
            for a, b in combinations(sorted(ids), 2):
                counts[(a, b)] += 1
    return counts


def build_same_author(driver: Driver, records: Sequence[dict]) -> int:
    author_to_ids: dict[str, set[int]] = defaultdict(set)
    for r in records:
        for a in r.get("authors") or []:
            key = a.strip().lower()
            if key:
                author_to_ids[key].add(r["id"])
    counts = _group_pairs(author_to_ids, SAME_AUTHOR_MAX_GROUP)
    triples = [(a, b, float(w)) for (a, b), w in counts.items()]
    return _load_weighted(driver, triples, "SAME_AUTHOR")


def build_co_listed(driver: Driver, records: Sequence[dict]) -> int:
    list_to_ids: dict[int, set[int]] = defaultdict(set)
    for r in records:
        for lid in r.get("recommendation_list_ids") or []:
            list_to_ids[lid].add(r["id"])
    counts = _group_pairs(list_to_ids, CO_LISTED_MAX_LIST)
    # require a minimum amount of co-listing
    strong = {p: w for p, w in counts.items() if w >= settings.co_listed_min_shared}
    # keep only each novel's top-k strongest neighbours (bounds node degree)
    by_node: dict[int, list[tuple[int, int]]] = defaultdict(list)  # node -> [(weight, other)]
    for (a, b), w in strong.items():
        by_node[a].append((w, b))
        by_node[b].append((w, a))
    keep: set[tuple[int, int]] = set()
    for node, neigh in by_node.items():
        for w, other in sorted(neigh, reverse=True)[:CO_LISTED_TOP_K]:
            keep.add((min(node, other), max(node, other)))
    triples = [(a, b, float(strong[(a, b)])) for (a, b) in keep]
    return _load_weighted(driver, triples, "CO_LISTED")


def build_content_similar(driver: Driver, records: Sequence[dict]) -> int:
    """Cosine kNN over TF-IDF vectors of (tags + genres). Each tag/genre is one atomic token."""
    from sklearn.feature_extraction.text import TfidfVectorizer

    ids = np.array([r["id"] for r in records])
    token_lists = [list(r.get("tags") or []) + list(r.get("genres") or []) for r in records]

    # analyzer=identity -> treat each tag/genre string as a single token (keeps multiword tags intact);
    # TF-IDF down-weights ubiquitous tags so rare shared tags drive similarity.
    vec = TfidfVectorizer(analyzer=lambda toks: toks, norm="l2")
    X = vec.fit_transform(token_lists)  # L2-normalized sparse matrix
    n = X.shape[0]
    k = settings.content_similar_top_k
    min_score = settings.content_similar_min_score

    best: dict[tuple[int, int], float] = {}
    batch = 1000
    for i in range(0, n, batch):
        sims = (X[i : i + batch] @ X.T).toarray()  # (b, n); cosine, since rows are L2-normalized
        for local, row in enumerate(sims):
            gi = i + local
            row[gi] = -1.0  # drop self-match
            top = np.argpartition(row, -k)[-k:] if k < n else np.arange(n)
            for j in top:
                score = float(row[j])
                if score >= min_score:
                    a, b = int(ids[gi]), int(ids[j])
                    if a == b:
                        continue
                    key = (a, b) if a < b else (b, a)
                    if key not in best or score > best[key]:
                        best[key] = score
    triples = [(a, b, w) for (a, b), w in best.items()]
    return _load_weighted(driver, triples, "SIMILAR")


def edge_counts(driver: Driver) -> dict[str, int]:
    out: dict[str, int] = {}
    with driver.session() as s:
        for rel in ("RELATED", "RECOMMENDS", "SAME_AUTHOR", "CO_LISTED", "SIMILAR"):
            out[rel] = s.run(f"MATCH ()-[r:{rel}]->() RETURN count(r) AS c").single()["c"]
    return out
