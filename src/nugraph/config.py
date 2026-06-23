"""Central configuration.

Values come from environment variables / a local `.env` file (see `.env.example`),
falling back to sensible localhost defaults. Importing `settings` anywhere gives a
single, validated config object.
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# repo root = two levels up from this file (src/nugraph/config.py -> repo root)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Neo4j (graph) ---
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "neo4j"

    # --- Qdrant (vectors) ---
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "novels"

    # --- Embeddings (local, CPU, free) ---
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384  # all-MiniLM-L6-v2 output size

    # --- Scraper politeness / resilience ---
    scrape_user_agent: str = "NUgraph/0.1 (personal research project)"
    # Very polite by default ("slowest as possible"). Tune via .env if needed.
    scrape_min_delay: float = 6.0    # seconds, randomized lower bound between requests
    scrape_max_delay: float = 15.0   # seconds, randomized upper bound between requests
    scrape_max_retries: int = 5

    # --- Graph edge-building thresholds (anti-hairball) ---
    content_similar_top_k: int = 10     # keep only the k most-similar per novel
    content_similar_min_score: float = 0.5
    co_listed_min_shared: int = 2       # require >= this many shared rec-lists

    # --- Paths ---
    data_dir: Path = DATA_DIR
    raw_dir: Path = DATA_DIR / "raw"
    processed_dir: Path = DATA_DIR / "processed"
    cache_dir: Path = DATA_DIR / "cache"


settings = Settings()
