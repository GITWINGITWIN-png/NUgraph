"""M3 entrypoint: scrape novel synopses (resumable).

    uv run python scripts/scrape_synopses.py --sample 5   # small validation run
    uv run python scripts/scrape_synopses.py              # full backfill (long, resumable)

Safe to Ctrl-C and re-run — it resumes from where it left off.
"""

from __future__ import annotations

import argparse

from nugraph.ingest import scraper
from nugraph.ingest import synopsis_store as store
from nugraph.ingest.dataset import load_records


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=None, help="only fetch N new novels (test run)")
    args = ap.parse_args()

    ids = [r["id"] for r in load_records()]
    stats = scraper.scrape(ids, limit=args.sample)
    print("\nStore status counts:", stats)
    ok = stats.get("ok", 0)
    print(f"Total descriptions captured so far: {ok:,} / {len(ids):,}")


if __name__ == "__main__":
    main()
