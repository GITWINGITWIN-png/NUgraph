# NUgraph

A relation graph over translated web novels from [NovelUpdates](https://www.novelupdates.com/),
plus **semantic "search by description"**.

- **Graph** — every novel is a node; edges come from related series, user recommendations,
  shared recommendation-lists, shared author/group, and content similarity. Stored in **Neo4j**.
- **Search** — novel synopses are embedded locally and indexed in **Qdrant** for
  natural-language similarity search.
- **Serve** — a **FastAPI** backend exposes search + graph endpoints; a **Vite + Cytoscape.js**
  frontend lets you search and explore each novel's neighborhood interactively.

Data is **dataset-first**: bulk metadata + relations come from the public
[`shaido987/novel-dataset`](https://github.com/shaido987/novel-dataset) (~24.6k novels);
a polite, cached scraper backfills the one missing field — the synopsis text.

## Data and site rules

- **The dataset** has no licence file, so this repo never copies it: the loader
  (`src/nugraph/ingest/dataset.py`) downloads it when you run it. No novel data, synopses or
  caches are committed; the data folders are ignored.
- **The synopsis scraper** (`scripts/scrape_synopses.py`) reads one field, `div#editdescription`,
  from each series page on novelupdates.com. It waits a random 6 to 15 seconds between requests,
  backs off on 403, 429 and 503, and can stop and resume without fetching a page twice. It uses
  `cloudscraper` because the site sits behind Cloudflare.
- **Site rules, checked on 24 November 2026:** robots.txt does not block the series pages, and the
  [Terms of Service](https://www.novelupdates.com/terms-of-service/) contain no clause against
  automated reading. Synopses stay on your machine. Check the rules again before you run it.

## Stack

| Concern        | Choice                                                |
|----------------|-------------------------------------------------------|
| Language       | Python 3.12 (managed by `uv`)                         |
| Graph DB       | Neo4j Community (native apt install)                  |
| Vector DB      | Qdrant (native binary + systemd)                      |
| Embeddings     | `sentence-transformers/all-MiniLM-L6-v2` (CPU, local) |
| Backend        | FastAPI + Uvicorn                                     |
| Frontend       | Vite + Cytoscape.js                                   |

## Setup

```bash
# 1. Install the databases (you run this; it uses sudo)
bash scripts/install_databases.sh

# 2. Configure secrets
cp .env.example .env          # then set NEO4J_PASSWORD

# 3. Python environment
uv sync                       # creates .venv with all deps

# 4. Health check
bash scripts/verify_databases.sh
```

## Removing the databases

```bash
sudo systemctl disable --now neo4j qdrant
sudo apt-get remove --purge neo4j
sudo rm -f /etc/systemd/system/qdrant.service /etc/apt/sources.list.d/neo4j.list
sudo rm -rf /opt/qdrant /var/lib/qdrant
sudo systemctl daemon-reload
```

---

Built with help from AI coding assistants.
