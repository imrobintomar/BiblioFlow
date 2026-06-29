from typing import Optional

from providers.base import MetadataProvider
from scopus.fetch import fetch_scopus_record


class ScopusProvider(MetadataProvider):
    """Thin wrapper around the existing scopus/fetch.py fetch function --
    delegates entirely, does not change extraction/verification behavior."""

    name = "scopus"

    def fetch_by_doi(self, doi: str) -> Optional[dict]:
        record = fetch_scopus_record(doi)
        return record.model_dump() if record else None
