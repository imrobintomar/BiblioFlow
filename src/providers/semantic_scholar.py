import time
from typing import Optional

import requests

from config import SEMANTIC_SCHOLAR_API_KEY
from providers.base import MetadataProvider

S2_BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/DOI:"
S2_FIELDS = "abstract,fieldsOfStudy,tldr,references.title,references.externalIds,citationCount,paperId"

# This key's grant is 1 request/second cumulative across all endpoints --
# throttle client-side so a burst of papers doesn't get rejected.
_MIN_INTERVAL_SECONDS = 1.1
_last_request_at = 0.0
_MAX_RETRIES = 3
_RETRY_BACKOFF_SECONDS = 3


def _throttle() -> None:
    global _last_request_at
    elapsed = time.monotonic() - _last_request_at
    if elapsed < _MIN_INTERVAL_SECONDS:
        time.sleep(_MIN_INTERVAL_SECONDS - elapsed)
    _last_request_at = time.monotonic()


class SemanticScholarProvider(MetadataProvider):
    """Free; uses an approved S2 API key (1 req/s cumulative) when present,
    falls back to the unauthenticated tier otherwise. Backfills abstract,
    fields of study, free AI-generated TLDR summaries, and references
    (with paper IDs that can be cross-referenced for citation context)."""

    name = "semantic_scholar"

    def fetch_by_doi(self, doi: str) -> Optional[dict]:
        headers = {"x-api-key": SEMANTIC_SCHOLAR_API_KEY} if SEMANTIC_SCHOLAR_API_KEY else {}

        response = None
        for attempt in range(_MAX_RETRIES):
            _throttle()
            response = requests.get(
                S2_BASE_URL + doi,
                params={"fields": S2_FIELDS},
                headers=headers,
                timeout=15,
            )
            if response.status_code != 429:
                break
            time.sleep(_RETRY_BACKOFF_SECONDS * (attempt + 1))

        if response.status_code == 404:
            return None
        response.raise_for_status()
        data = response.json()

        references = [
            {
                "title": r.get("title"),
                "doi": (r.get("externalIds") or {}).get("DOI"),
            }
            for r in (data.get("references") or [])
        ]

        return {
            "abstract": data.get("abstract"),
            "fields_of_study": data.get("fieldsOfStudy") or [],
            "tldr": (data.get("tldr") or {}).get("text"),
            "references": references,
            "citation_count": data.get("citationCount"),
            "semantic_scholar_id": data.get("paperId"),
        }
