import json
from pathlib import Path
from typing import Optional

from config import CACHE_DIR

SCOPUS_CACHE_DIR = CACHE_DIR / "scopus"
SCOPUS_CACHE_DIR.mkdir(exist_ok=True)


def _cache_path(doi: str) -> Path:
    safe_name = doi.replace("/", "_")
    return SCOPUS_CACHE_DIR / f"{safe_name}.json"


def load_cached(doi: str) -> Optional[dict]:
    path = _cache_path(doi)
    if path.exists():
        return json.loads(path.read_text())
    return None


def save_cache(doi: str, data: dict) -> None:
    _cache_path(doi).write_text(json.dumps(data, indent=2, default=str))
