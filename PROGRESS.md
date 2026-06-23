# NUgraph — progress tracker

Live status of the build. Full plan: `~/.claude/plans/i-want-to-extract-humble-cocke.md`.

_Last updated: 2026-06-23_

## Milestones

| # | Milestone | Status | Notes |
|---|-----------|--------|-------|
| M0 | Project scaffold + `uv` (Python 3.12) | ✅ done | `src/nugraph/`, `pyproject.toml`, `config.py` |
| —  | Install Neo4j + Qdrant (native, systemd) | ✅ done | both services `active` |
| M1 | Load novel nodes into Neo4j | ✅ done | **24,639** `:Novel` nodes |
| M2 | Build relationship edges | ✅ done | **~140k edges**: RECOMMENDS 60,155 · SIMILAR 39,967 · SAME_AUTHOR 24,281 · CO_LISTED 11,971 · RELATED 3,940 |
| M3 | Synopsis scraper (polite/cached/resumable) | 🟢 running | Built + validated (5/5 sample ok). **Full backfill running in background** (~24.6k novels, ~6–15s each). |
| M4 | Embed synopses → Qdrant + semantic search | ✅ done | 24,639 indexed; strong results even on tag/genre fallback. Re-run `build_search.py` to fold in synopses as they scrape. |
| M5 | FastAPI backend (search + graph endpoints) | ⬜ next | |
| M6 | Vite + Cytoscape.js frontend | ⬜ todo | |
| M7 | (future) full live scraper **+ recommendation-list membership** | ⬜ deferred | See "Recommendations" note below. |

## Recommendations & recommendation lists (investigated 2026-06-23)
- **Recommendation chain — DONE.** NU caps on-page recommendations at 6; we have them as
  `RECOMMENDS` edges. Chains are just multi-hop traversal, e.g.:
  `MATCH p=(a:Novel {id:5})-[:RECOMMENDS*1..3]->(b) RETURN p`.
- **Recommendation-list membership — deferred (M7).** It's AJAX-loaded; the simple URL routes
  don't work (`?p=<id>` → a novel; `series-finder?list=<id>` ignores the filter and returns the
  full catalog). Getting it needs headless-browser endpoint discovery + a separate ~12k-page
  crawl. We keep the **partial** `CO_LISTED` (11,971 edges from the dataset's capped 5 lists/novel)
  for now. Decision: build the core search pipeline first.

## M3 scraper facts (settled)
- Fetch `https://www.novelupdates.com/?p=<id>`; synopsis is `div#editdescription`. Synopsis only.
- `cloudscraper` (Cloudflare-aware); long randomized delays; exp. backoff on 403/429/503; resumable.
- Store: `data/processed/synopses.sqlite` (status: ok / empty / notfound / error). M4 reads `ok` rows.

## Useful commands
- Scrape status: `uv run python -c "from nugraph.ingest import synopsis_store as s; print(s.stats())"`
- Resume scrape:  `uv run python scripts/scrape_synopses.py`
- Neo4j Browser:  http://localhost:7474   ·   Qdrant: http://localhost:6333/dashboard
