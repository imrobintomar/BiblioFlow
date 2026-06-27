import time
from typing import Optional

import requests

from config import CROSSREF_BASE_URL, CROSSREF_MAILTO

_SESSION = requests.Session()
_MAX_RETRIES = 3
_RETRY_BACKOFF_SECONDS = 2


def fetch_crossref_record(doi: str) -> Optional[dict]:
    url = f"{CROSSREF_BASE_URL}/{doi}"
    params = {"mailto": CROSSREF_MAILTO}

    for attempt in range(_MAX_RETRIES):
        response = _SESSION.get(url, params=params, timeout=15)
        if response.status_code == 200:
            return response.json().get("message")
        if response.status_code == 404:
            return None
        if response.status_code == 429:
            time.sleep(_RETRY_BACKOFF_SECONDS * (attempt + 1))
            continue
        response.raise_for_status()
    return None
