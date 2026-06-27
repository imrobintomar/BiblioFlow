from models import ScopusRecord


def parse_search_entry(doi: str, entry: dict) -> ScopusRecord:
    """Maps a Scopus Search API entry to our ScopusRecord.

    The Search API (works with a non-subscriber API key) only returns the
    first author via dc:creator and no abstract/keywords/references --
    those fields require Abstract Retrieval, which needs institutional
    (IP or insttoken) access.
    """
    first_author = entry.get("dc:creator")
    authors = [first_author] if first_author else []

    affiliations = [
        aff.get("affilname")
        for aff in entry.get("affiliation", [])
        if aff.get("affilname")
    ]

    cited_by = entry.get("citedby-count")

    return ScopusRecord(
        doi=doi,
        eid=entry.get("eid"),
        title=entry.get("dc:title"),
        authors=authors,
        affiliations=affiliations,
        abstract=None,
        keywords=[],
        cited_by_count=int(cited_by) if cited_by is not None else None,
        source_title=entry.get("prism:publicationName"),
        publication_date=entry.get("prism:coverDate"),
        references=[],
        raw=None,
    )
