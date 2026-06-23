"""M3: polite, cached, resumable scraper for novel **synopses only**.

For each novel id we fetch `https://www.novelupdates.com/?p=<id>` (redirects to the series
page) and extract the text of `div#editdescription`. Nothing else is collected.

Good-citizen behaviour:
- `cloudscraper` (Cloudflare-aware) — the same approach the original dataset scraper used.
  We let it manage the browser User-Agent (needed to pass Cloudflare); politeness comes from
  the long delays below, not from hammering.
- Long randomized delay between requests (config: `scrape_min_delay`..`scrape_max_delay`).
- Exponential backoff on 403/429/503 (treated as "slow down" signals), capped retries.
- Resumable: progress is written to `synopsis_store` after every novel, so stopping/restarting
  never re-fetches a page.
"""

from __future__ import annotations

import random
import time
from collections.abc import Iterable, Sequence

import cloudscraper
from bs4 import BeautifulSoup
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from tqdm import tqdm

from ..config import settings
from . import synopsis_store as store

SERIES_URL = "https://www.novelupdates.com/?p={id}"


class Blocked(Exception):
    """Raised on 403/429/503 so tenacity backs off and retries."""


def make_scraper() -> "cloudscraper.CloudScraper":
    return cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "linux", "mobile": False}
    )


@retry(
    retry=retry_if_exception_type(Blocked),
    wait=wait_exponential(multiplier=5, min=10, max=300),  # 10s,20s,40s... capped at 5min
    stop=stop_after_attempt(settings.scrape_max_retries),
    reraise=True,
)
def _get(scraper, url: str):
    resp = scraper.get(url, timeout=30)
    if resp.status_code in (403, 429, 503):
        raise Blocked(f"HTTP {resp.status_code}")
    resp.raise_for_status()
    return resp


def fetch_description(scraper, novel_id: int) -> tuple[str | None, str]:
    """Return (description_text_or_None, status). status in ok/empty/notfound."""
    resp = _get(scraper, SERIES_URL.format(id=novel_id))
    soup = BeautifulSoup(resp.text, "html.parser")
    div = soup.find("div", id="editdescription")
    if div is None:
        return None, "notfound"  # id redirected somewhere without a synopsis block
    text = div.get_text("\n", strip=True)
    if not text or text.strip().upper() == "N/A":  # NU's placeholder for "no synopsis"
        return None, "empty"
    return text, "ok"


def scrape(ids: Sequence[int], limit: int | None = None) -> dict[str, int]:
    """Scrape synopses for the given novel ids, skipping ones already attempted.

    `limit` caps how many *new* novels to fetch this run (handy for a small sample test).
    """
    already = store.done_ids()
    todo: Iterable[int] = [i for i in ids if i not in already]
    if limit is not None:
        todo = list(todo)[:limit]
    else:
        todo = list(todo)

    print(f"{len(already):,} already done; {len(todo):,} to fetch this run.")
    scraper = make_scraper()
    for novel_id in tqdm(todo, desc="synopses", unit="novel"):
        try:
            desc, status = fetch_description(scraper, novel_id)
        except Exception as exc:  # noqa: BLE001 — record and keep going
            desc, status = None, "error"
            tqdm.write(f"  id={novel_id}: {type(exc).__name__}: {exc}")
        store.upsert(novel_id, desc, status)
        # polite pause (skipped after the final item)
        if novel_id != todo[-1]:
            time.sleep(random.uniform(settings.scrape_min_delay, settings.scrape_max_delay))

    return store.stats()
