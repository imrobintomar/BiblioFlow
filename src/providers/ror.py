from typing import Optional

import requests

ROR_BASE_URL = "https://api.ror.org/organizations"


class RorProvider:
    """Free, no key. Used as institution-name backfill when OpenAlex didn't
    already resolve a country for an institution string extracted from the
    PDF/Scopus affiliation text."""

    name = "ror"

    def resolve_by_name(self, institution_name: str) -> Optional[dict]:
        response = requests.get(ROR_BASE_URL, params={"query": institution_name}, timeout=15)
        response.raise_for_status()
        items = response.json().get("items", [])
        if not items:
            return None

        item = items[0]
        locations = item.get("locations") or []
        country = locations[0]["geonames_details"]["country_name"] if locations else None

        display_name = next(
            (n["value"] for n in item.get("names", []) if "ror_display" in n.get("types", [])),
            institution_name,
        )

        return {"name": display_name, "country": country, "ror_id": item.get("id")}
