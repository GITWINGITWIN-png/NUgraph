# NUgraph

A relation graph of about 25,000 translated web novels listed on [NovelUpdates](https://www.novelupdates.com/), with search by description. Each novel is a node in Neo4j, linked to others through user recommendations, content similarity, a shared author or group, shared recommendation lists and related series, about 140,000 edges in all. Synopses are embedded locally and indexed in Qdrant, so you can describe a story in plain language and get the closest matches. A FastAPI backend serves search and graph queries, and a Vite and Cytoscape.js page lets you explore each novel's neighbours.

## Data and site rules

The novel metadata and relations come from [`shaido987/novel-dataset`](https://github.com/shaido987/novel-dataset). That dataset has no licence file, so this repo never copies it: `src/nugraph/ingest/dataset.py` downloads it when you run the loader. The data folders are ignored, and no novel data or synopses are committed.

The dataset has no synopses, so `scripts/scrape_synopses.py` reads one field, `div#editdescription`, from each series page on novelupdates.com. It waits a random 6 to 15 seconds between requests, backs off on 403, 429 and 503 responses, and resumes without fetching a page twice. It uses `cloudscraper` because the site is behind Cloudflare. On 24 November 2026, robots.txt did not block the series pages and the [Terms of Service](https://www.novelupdates.com/terms-of-service/) had no clause against automated reading. Check them again before you run it.

## Setup

```bash
bash scripts/install_databases.sh   # Neo4j and Qdrant as system services (uses sudo)
cp .env.example .env                # then set NEO4J_PASSWORD
uv sync
bash scripts/verify_databases.sh
```

## Build and run

```bash
uv run python scripts/load_graph.py        # novels into Neo4j
uv run python scripts/build_edges.py       # the relation edges
uv run python scripts/scrape_synopses.py   # synopsis backfill; --sample N for a test run
uv run python scripts/build_search.py      # embed and index in Qdrant; rerun after new synopses
uv run uvicorn nugraph.api.main:app --port 8001
cd frontend && npm install && npm run dev  # http://localhost:5180
```

Search works before the backfill finishes, because novels without a synopsis are embedded from their tags and genres until the next `build_search.py` run. Embeddings use `sentence-transformers/all-MiniLM-L6-v2` on the CPU.

To remove the databases:

```bash
sudo systemctl disable --now neo4j qdrant
sudo apt-get remove --purge neo4j
sudo rm -f /etc/systemd/system/qdrant.service /etc/apt/sources.list.d/neo4j.list
sudo rm -rf /opt/qdrant /var/lib/qdrant
sudo systemctl daemon-reload
```
