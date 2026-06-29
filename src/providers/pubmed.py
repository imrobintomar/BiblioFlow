import xml.etree.ElementTree as ET
from typing import Optional

import requests

ID_CONVERTER_URL = "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


class PubMedProvider:
    """Free, API key recommended for >3 req/s. Conditional -- only useful
    for biomedical papers that resolve to a PMID. Gives MeSH terms (a
    strong biomedical keyword taxonomy), grant IDs, structured abstract."""

    name = "pubmed"

    def resolve_pmid(self, doi: str) -> Optional[str]:
        response = requests.get(ID_CONVERTER_URL, params={"ids": doi, "format": "json"}, timeout=15)
        response.raise_for_status()
        records = response.json().get("records", [])
        if records and "pmid" in records[0]:
            return records[0]["pmid"]
        return None

    def fetch_by_pmid(self, pmid: str) -> Optional[dict]:
        response = requests.get(
            EFETCH_URL,
            params={"db": "pubmed", "id": pmid, "rettype": "abstract", "retmode": "xml"},
            timeout=15,
        )
        response.raise_for_status()
        root = ET.fromstring(response.content)

        article = root.find(".//PubmedArticle")
        if article is None:
            return None

        mesh_terms = [
            d.text for d in article.findall(".//MeshHeading/DescriptorName") if d.text
        ]
        grant_ids = [g.text for g in article.findall(".//Grant/GrantID") if g.text]
        abstract_parts = [a.text for a in article.findall(".//Abstract/AbstractText") if a.text]

        return {
            "pmid": pmid,
            "mesh_terms": mesh_terms,
            "grant_ids": grant_ids,
            "abstract": " ".join(abstract_parts) if abstract_parts else None,
        }
