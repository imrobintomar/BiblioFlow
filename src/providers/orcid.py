from typing import Optional

import requests

ORCID_BASE_URL = "https://pub.orcid.org/v3.0/"


class OrcidProvider:
    """Free, no key, public data only. Enriches an author profile once an
    ORCID is already known (from PDF byline regex or OpenAlex authorship
    data) -- not a per-paper gap-filler, used for author profile lookups."""

    name = "orcid"

    def fetch_by_orcid(self, orcid_id: str) -> Optional[dict]:
        orcid_id = orcid_id.rstrip("/").rsplit("/", 1)[-1]
        response = requests.get(
            ORCID_BASE_URL + orcid_id,
            headers={"Accept": "application/json"},
            timeout=15,
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        data = response.json()
        person = data.get("person", {})
        name = person.get("name", {})

        return {
            "orcid": orcid_id,
            "given_name": (name.get("given-names") or {}).get("value"),
            "family_name": (name.get("family-name") or {}).get("value"),
            "credit_name": (name.get("credit-name") or {}).get("value"),
        }
