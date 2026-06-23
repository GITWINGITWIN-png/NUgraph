"""Acquire the base dataset.

Bulk metadata + relations come from the public `shaido987/novel-dataset`
(~24.6k novels). We use the JSON form because it preserves nested arrays
(genres, tags, related-series ids) cleanly.
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

from ..config import settings

DATASET_VERSION = "0.1.5"
_RAW_BASE = "https://raw.githubusercontent.com/shaido987/novel-dataset/master"
JSON_NAME = f"novels_{DATASET_VERSION}.json"


def dataset_path() -> Path:
    return settings.raw_dir / JSON_NAME


def download_dataset(force: bool = False) -> Path:
    """Download the dataset JSON into data/raw/ (idempotent — skips if present)."""
    dest = dataset_path()
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and not force:
        return dest
    url = f"{_RAW_BASE}/{JSON_NAME}"
    print(f"Downloading {url} -> {dest}")
    urllib.request.urlretrieve(url, dest)
    return dest


def load_records() -> list[dict]:
    """Load the dataset as a list of novel dicts."""
    return json.loads(dataset_path().read_text(encoding="utf-8"))
