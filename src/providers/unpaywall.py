from typing import Optional

import requests

from config import CROSSREF_MAILTO
from providers.base import MetadataProvider

UNPAYWALL_BASE_URL = "https://api.unpaywall.org/v2/"


class UnpaywallProvider(MetadataProvider):
    """Free, just a `mailto`. OA status confirmation and -- more useful for
    'don't miss publicly available data' -- a legal full-text PDF URL for
    papers not already downloaded locally."""

    name = "unpaywall"

    def fetch_by_doi(self, doi: str) -> Optional[dict]:
        response = requests.get(
            UNPAYWALL_BASE_URL + doi,
            params={"email": CROSSREF_MAILTO},
            timeout=15,
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        data = response.json()

        best = data.get("best_oa_location") or {}
        return {
            "is_oa": data.get("is_oa"),
            "oa_status": data.get("oa_status"),
            "oa_url": best.get("url_for_pdf") or best.get("url"),
        }
