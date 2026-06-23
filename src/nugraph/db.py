"""Database client factories — one place that knows how to reach Neo4j and Qdrant.

Everything else imports from here so connection details live in exactly one spot.
"""

from __future__ import annotations

from contextlib import contextmanager
from collections.abc import Iterator
from functools import lru_cache

from neo4j import Driver, GraphDatabase, Session
from qdrant_client import QdrantClient

from .config import settings


def get_neo4j_driver() -> Driver:
    """Return a Neo4j driver. Caller is responsible for `.close()` (or use `neo4j_session`)."""
    return GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )


@contextmanager
def neo4j_session() -> Iterator[Session]:
    """Context manager yielding a Neo4j session and cleaning up the driver afterwards."""
    driver = get_neo4j_driver()
    try:
        with driver.session() as session:
            yield session
    finally:
        driver.close()


def get_qdrant() -> QdrantClient:
    """Return a Qdrant client pointed at the configured URL."""
    return QdrantClient(url=settings.qdrant_url)


# --- long-lived shared singletons (for the API; drivers/clients are thread-safe) ---
@lru_cache(maxsize=1)
def shared_driver() -> Driver:
    return get_neo4j_driver()


@lru_cache(maxsize=1)
def shared_qdrant() -> QdrantClient:
    return get_qdrant()
