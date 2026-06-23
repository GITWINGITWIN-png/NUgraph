"""M2 entrypoint: build all relationship edges + report counts and a sample neighborhood.

    uv run python scripts/build_edges.py
"""

from __future__ import annotations

import time

from nugraph.db import get_neo4j_driver
from nugraph.graph import edges
from nugraph.ingest.dataset import load_records


def main() -> None:
    records = load_records()
    driver = get_neo4j_driver()
    try:
        steps = [
            ("RELATED", edges.build_related),
            ("RECOMMENDS", edges.build_recommends),
            ("SAME_AUTHOR", edges.build_same_author),
            ("CO_LISTED", edges.build_co_listed),
            ("SIMILAR (tags/genres)", edges.build_content_similar),
        ]
        for name, fn in steps:
            t0 = time.perf_counter()
            n = fn(driver, records)
            print(f"  {name:24} built {n:>8,} edges  ({time.perf_counter()-t0:5.1f}s)")

        print("\nEdge counts in Neo4j:")
        for rel, c in edges.edge_counts(driver).items():
            print(f"  {rel:14} {c:>9,}")

        # sanity check: neighborhood of "Coiling Dragon" (id=5)
        print("\nSample — relations of 'Coiling Dragon' (id=5), by type:")
        with driver.session() as s:
            rows = s.run(
                """
                MATCH (n:Novel {id: 5})-[r]-(m:Novel)
                RETURN type(r) AS rel, m.name AS name, r.weight AS weight
                ORDER BY rel, coalesce(r.weight, 1.0) DESC
                LIMIT 25
                """
            ).data()
            for row in rows:
                w = f"{row['weight']:.2f}" if row["weight"] is not None else "-"
                print(f"  {row['rel']:12} {w:>5}  {row['name']}")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
