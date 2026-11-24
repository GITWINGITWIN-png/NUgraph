# NUgraph — progress tracker

Live status of the build.

_Last updated: 2026-06-23_

## Status: core product complete ✅
Both goals work end-to-end through a web UI: **relation graph** (Neo4j) + **search by
description** (Qdrant). The synopsis backfill keeps running in the background and makes search
sharper over time.

## Milestones

| # | Milestone | Status | Notes |
|---|-----------|--------|-------|
| M0 | Scaffold + `uv` (Python 3.12) | ✅ done | |
| —  | Install Neo4j + Qdrant (native systemd) | ✅ done | |
| M1 | Novel nodes → Neo4j | ✅ done | 24,639 `:Novel` nodes |
| M2 | Relationship edges | ✅ done | ~140k: RECOMMENDS 60,155, SIMILAR 39,967, SAME_AUTHOR 24,281, CO_LISTED 11,971, RELATED 3,940 |
| M3 | Synopsis scraper | 🟢 running | Resumable backfill in background (~24.6k novels, polite pace). |
| M4 | Semantic search (Qdrant) | ✅ done | 24,639 indexed; re-run `build_search.py` to fold in new synopses |
| M5 | FastAPI backend | ✅ done | search / novel / graph-neighbors / facets — on **:8001** |
| M6 | React + Vite + Cytoscape.js UI | ✅ done | on **:5180** |
| M7 | (future) full live scraper + recommendation-list membership | ⬜ deferred | see note below |

## How to run (all local)

| Service | Command | URL |
|---|---|---|
| Neo4j (graph) | `systemctl status neo4j` (auto-starts) | http://localhost:7474 |
| Qdrant (vectors) | `systemctl status qdrant` (auto-starts) | http://localhost:6333/dashboard |
| API backend | `uv run uvicorn nugraph.api.main:app --port 8001` | http://localhost:8001/docs |
| Frontend | `cd frontend && npm run dev` | http://localhost:5180 |

> NUgraph uses ports **8001** and **5180** so it can run next to other local apps on the default ports.

## Pipeline scripts
- `scripts/load_graph.py`   — M1: dataset → Neo4j nodes
- `scripts/build_edges.py`  — M2: build all edges
- `scripts/scrape_synopses.py` — M3: synopsis backfill (resumable; `--sample N` for a test)
- `scripts/build_search.py` — M4: (re)build the Qdrant index (re-run to fold in new synopses)

## Recommendations & lists (decided 2026-06-23)
- **Chain — done**: multi-hop over `RECOMMENDS` (NU caps recs at 6/page; we have them).
- **Rec-list membership — deferred (M7)**: AJAX-loaded; needs headless-browser endpoint discovery
  + a ~12k-page crawl. We keep the partial `CO_LISTED` for now.

## Next steps
1. Let the synopsis scrape finish, then re-run `build_search.py` to upgrade tag-based vectors to
   real-synopsis vectors (the `has_synopsis` flag flips true).
2. (Optional, M7) recommendation-list membership; full live refresh + scheduling.
