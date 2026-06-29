import logging

import pycountry

from providers.openalex import OpenAlexProvider
from providers.pubmed import PubMedProvider
from providers.ror import RorProvider
from providers.semantic_scholar import SemanticScholarProvider
from providers.unpaywall import UnpaywallProvider
from repository.paper_repository import PaperRepository
from repository.provenance_repository import ProvenanceRepository

logger = logging.getLogger("enrichment")

_TOP_CONCEPTS_AS_KEYWORDS = 8


def _country_name(country_code: str | None) -> str | None:
    if not country_code:
        return None
    country = pycountry.countries.get(alpha_2=country_code)
    return country.name if country else country_code


def _canonical_country_name(raw_name: str) -> str:
    """Normalizes country name strings across sources (ROR's 'The
    Netherlands' vs OpenAlex/pycountry's 'Netherlands', etc.) so the same
    country isn't fragmented into multiple entries."""
    try:
        return pycountry.countries.search_fuzzy(raw_name)[0].name
    except LookupError:
        return raw_name


class EnrichmentService:
    """Free-API waterfall run after the (unmodified) extraction pipeline +
    Docling/regex extraction. Each provider only fills fields still empty --
    never overwrites a value an earlier, higher-priority source already set.
    Order: OpenAlex -> Semantic Scholar -> PubMed (conditional) -> Unpaywall
    -> ROR (institution-country backfill only). Scopus/CrossRef already ran
    inside the unmodified pipeline before this is called."""

    def __init__(self):
        self.openalex = OpenAlexProvider()
        self.semantic_scholar = SemanticScholarProvider()
        self.pubmed = PubMedProvider()
        self.unpaywall = UnpaywallProvider()
        self.ror = RorProvider()

    def enrich_paper(self, conn, paper_id: int, doi: str | None) -> None:
        if not doi:
            return

        papers = PaperRepository(conn)
        provenance = ProvenanceRepository(conn)

        pmid = None
        try:
            oa_data = self.openalex.fetch_by_doi(doi)
        except Exception as exc:  # noqa: BLE001
            logger.warning("OpenAlex failed for %s: %s", doi, exc)
            oa_data = None

        if oa_data:
            papers.update_fields_if_empty(
                paper_id,
                abstract=oa_data.get("abstract"),
                pmid=oa_data.get("pmid"),
                oa_url=oa_data.get("oa_url"),
                open_access=1 if oa_data.get("open_access") else None,
            )
            pmid = oa_data.get("pmid")

            if oa_data.get("concepts"):
                papers.add_keywords(paper_id, oa_data["concepts"][:_TOP_CONCEPTS_AS_KEYWORDS])
                provenance.record(paper_id, "keywords", "openalex", "concepts", 0.7)

            institutions = [
                {"name": i["name"], "country": _country_name(i.get("country_code"))}
                for i in oa_data.get("institutions", [])
                if i.get("name")
            ]
            if institutions:
                papers.add_institutions_with_country(paper_id, institutions)
                if any(i["country"] for i in institutions):
                    provenance.record(paper_id, "country", "openalex", "authorships.institutions", 0.9)

            if oa_data.get("grants"):
                papers.add_funders(
                    paper_id,
                    [
                        {"name": g["funder"], "grant_id": g.get("award_id")}
                        for g in oa_data["grants"]
                        if g.get("funder")
                    ],
                )
                provenance.record(paper_id, "funding", "openalex", "grants", 0.9)

            if oa_data.get("referenced_works"):
                papers.add_references(
                    paper_id,
                    [{"doi": None, "raw_text": w} for w in oa_data["referenced_works"]],
                )
                provenance.record(paper_id, "references", "openalex", "referenced_works", 0.6)

            if oa_data.get("abstract"):
                provenance.record(paper_id, "abstract", "openalex", "abstract_inverted_index", 0.8)
            if oa_data.get("oa_url"):
                provenance.record(paper_id, "open_access", "openalex", "open_access", 0.9)

        try:
            s2_data = self.semantic_scholar.fetch_by_doi(doi)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Semantic Scholar failed for %s: %s", doi, exc)
            s2_data = None

        if s2_data:
            papers.update_fields_if_empty(
                paper_id,
                abstract=s2_data.get("abstract"),
                semantic_scholar_id=s2_data.get("semantic_scholar_id"),
            )
            current_abstract = papers.get_field(paper_id, "abstract")
            if s2_data.get("abstract") and current_abstract not in (None, ""):
                provenance.record(paper_id, "abstract", "semantic_scholar", "graph_api", 0.75)

            doi_refs = [r for r in (s2_data.get("references") or []) if r.get("doi")]
            if doi_refs:
                papers.add_references(
                    paper_id, [{"doi": r["doi"], "raw_text": r.get("title")} for r in doi_refs]
                )
                provenance.record(paper_id, "references", "semantic_scholar", "references", 0.85)

            if s2_data.get("fields_of_study"):
                papers.add_keywords(paper_id, s2_data["fields_of_study"])

        if not pmid:
            try:
                pmid = self.pubmed.resolve_pmid(doi)
            except Exception as exc:  # noqa: BLE001
                logger.warning("PubMed ID resolution failed for %s: %s", doi, exc)

        if pmid:
            try:
                pubmed_data = self.pubmed.fetch_by_pmid(pmid)
            except Exception as exc:  # noqa: BLE001
                logger.warning("PubMed fetch failed for pmid %s: %s", pmid, exc)
                pubmed_data = None

            if pubmed_data:
                papers.update_fields_if_empty(paper_id, abstract=pubmed_data.get("abstract"), pmid=pmid)
                if pubmed_data.get("mesh_terms"):
                    papers.add_keywords(paper_id, pubmed_data["mesh_terms"])
                    provenance.record(paper_id, "keywords", "pubmed", "mesh_terms", 0.95)

        if not papers.get_field(paper_id, "oa_url"):
            try:
                up_data = self.unpaywall.fetch_by_doi(doi)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Unpaywall failed for %s: %s", doi, exc)
                up_data = None

            if up_data:
                papers.update_fields_if_empty(
                    paper_id,
                    oa_url=up_data.get("oa_url"),
                    open_access=1 if up_data.get("is_oa") else None,
                )
                if up_data.get("oa_url"):
                    provenance.record(paper_id, "open_access", "unpaywall", "best_oa_location", 0.9)

    def backfill_institution_countries(self, conn) -> None:
        """Run once per import batch (not per paper) -- backfills country
        for any institution OpenAlex didn't already resolve."""
        papers = PaperRepository(conn)
        rows = conn.execute(
            "SELECT id, name FROM institutions WHERE country_id IS NULL"
        ).fetchall()
        for row in rows:
            try:
                resolved = self.ror.resolve_by_name(row["name"])
            except Exception as exc:  # noqa: BLE001
                logger.warning("ROR lookup failed for %s: %s", row["name"], exc)
                continue
            if resolved and resolved.get("country"):
                country_id = papers.countries.get_or_create(_canonical_country_name(resolved["country"]))
                conn.execute(
                    "UPDATE institutions SET country_id = ? WHERE id = ?",
                    (country_id, row["id"]),
                )
