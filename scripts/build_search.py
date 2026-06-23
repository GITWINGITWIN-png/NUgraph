"""M4 entrypoint: (re)build the Qdrant semantic index and smoke-test a few queries.

    uv run python scripts/build_search.py

Re-run anytime to fold in newly-scraped synopses (it upserts).
"""

from __future__ import annotations

from nugraph.ingest import synopsis_store as store
from nugraph.search.index import build_index, search


def main() -> None:
    print("Synopsis scrape so far:", store.stats())
    n, with_syn = build_index(recreate=True)
    print(f"\nIndexed {n:,} novels  ({with_syn:,} with real synopsis, rest tag/genre fallback)\n")

    for q in [
        "cultivation revenge betrayal sect",
        "villainess reincarnated into an otome game",
        "system litrpg dungeon leveling up",
    ]:
        print(f"Q: {q!r}")
        for r in search(q, k=5):
            flag = "SYN" if r.get("has_synopsis") else "tag"
            print(f"   [{flag}] {r['score']:.3f}  {r['name']}  ({r.get('language')})")
        print()


if __name__ == "__main__":
    main()
