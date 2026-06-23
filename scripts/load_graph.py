"""M1 entrypoint: download the dataset and load novel nodes into Neo4j.

    uv run python scripts/load_graph.py
"""

from __future__ import annotations

from nugraph.db import get_neo4j_driver
from nugraph.graph.loader import ensure_constraints, load_novels, novel_count
from nugraph.ingest.dataset import download_dataset, load_records


def main() -> None:
    download_dataset()
    records = load_records()
    print(f"Loaded {len(records)} records from dataset.")

    driver = get_neo4j_driver()
    try:
        ensure_constraints(driver)
        n = load_novels(driver, records)
        print(f"Upserted {n} :Novel nodes.")
        print(f"Total :Novel nodes now in Neo4j: {novel_count(driver)}")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
