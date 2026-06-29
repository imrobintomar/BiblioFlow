from typing import Optional

from providers.base import MetadataProvider
from verify.crossref import fetch_crossref_record


class CrossrefProvider(MetadataProvider):
    """Thin wrapper around the existing verify/crossref.py fetch function --
    delegates entirely, does not change extraction/verification behavior."""

    name = "crossref"

    def fetch_by_doi(self, doi: str) -> Optional[dict]:
        return fetch_crossref_record(doi)
