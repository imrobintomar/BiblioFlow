from typing import Optional

import requests

from config import CROSSREF_MAILTO
from providers.base import MetadataProvider

OPENALEX_BASE_URL = "https://api.openalex.org/works/https://doi.org/"


def _reconstruct_abstract(inverted_index: Optional[dict]) -> Optional[str]:
    if not inverted_index:
        return None
    positions: list[tuple[int, str]] = []
    for word, idxs in inverted_index.items():
        for idx in idxs:
            positions.append((idx, word))
    positions.sort()
    return " ".join(word for _, word in positions)


class OpenAlexProvider(MetadataProvider):
    """Free, no-key. Fills Country, normalized Institutions+ROR, Concepts
    (keyword substitute), Abstract backfill, references, grants, OA status."""

    name = "openalex"

    def fetch_by_doi(self, doi: str) -> Optional[dict]:
        response = requests.get(
            OPENALEX_BASE_URL + doi,
            params={"mailto": CROSSREF_MAILTO},
            timeout=15,
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        data = response.json()

        authors = []
        institutions = []
        for authorship in data.get("authorships", []):
            author = authorship.get("author", {})
            authors.append(
                {
                    "name": author.get("display_name"),
                    "orcid": author.get("orcid"),
                }
            )
            for inst in authorship.get("institutions", []):
                institutions.append(
                    {
                        "name": inst.get("display_name"),
                        "country_code": inst.get("country_code"),
                        "ror": inst.get("ror"),
                    }
                )

        grants = [
            {
                "funder": g.get("funder_display_name"),
                "award_id": g.get("award_id"),
            }
            for g in (data.get("grants") or [])
        ]

        return {
            "title": data.get("title"),
            "abstract": _reconstruct_abstract(data.get("abstract_inverted_index")),
            "authors": authors,
            "institutions": institutions,
            "concepts": [c.get("display_name") for c in data.get("concepts", [])],
            "referenced_works": data.get("referenced_works", []),
            "grants": grants,
            "cited_by_count": data.get("cited_by_count"),
            "open_access": (data.get("open_access") or {}).get("is_oa"),
            "oa_url": (data.get("open_access") or {}).get("oa_url"),
            "pmid": (data.get("ids") or {}).get("pmid", "").rsplit("/", 1)[-1] or None,
            "openalex_id": data.get("id"),
        }
