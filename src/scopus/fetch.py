from typing import Optional

import requests

from config import SCOPUS_API_KEY
from models import ScopusRecord
from scopus.cache import load_cached, save_cache
from scopus.parser import parse_search_entry

SEARCH_URL = "https://api.elsevier.com/content/search/scopus"


def fetch_scopus_record(doi: str, use_cache: bool = True) -> Optional[ScopusRecord]:
    if use_cache:
        cached = load_cached(doi)
        if cached is not None:
            return ScopusRecord(**cached)

    if not SCOPUS_API_KEY:
        raise RuntimeError("SCOPUS_API_KEY not found in scopus_api.env")

    response = requests.get(
        SEARCH_URL,
        params={"query": f"DOI({doi})"},
        headers={"X-ELS-APIKey": SCOPUS_API_KEY, "Accept": "application/json"},
        timeout=15,
    )
    response.raise_for_status()
    entries = response.json().get("search-results", {}).get("entry", [])

    if not entries or "error" in entries[0]:
        return None

    record = parse_search_entry(doi, entries[0])
    save_cache(doi, record.model_dump())
    return record
