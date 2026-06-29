from config import TITLE_FUZZY_MATCH_THRESHOLD
from models import CrossrefVerification, ExtractedRecord
from verify.crossref import fetch_crossref_record
from verify.fuzzy import title_similarity


def verify_doi(extracted: ExtractedRecord) -> CrossrefVerification | None:
    if not extracted.extracted_doi:
        return None

    record = fetch_crossref_record(extracted.extracted_doi)
    if record is None:
        return None

    crossref_title = (record.get("title") or [None])[0]
    authors = [
        f"{a.get('given', '')} {a.get('family', '')}".strip()
        for a in record.get("author", [])
    ]
    journal = (record.get("container-title") or [None])[0]
    year = None
    date_parts = record.get("published-print") or record.get("published-online") or {}
    parts = date_parts.get("date-parts", [[None]])
    if parts and parts[0]:
        year = parts[0][0]

    score = title_similarity(extracted.extracted_title or "", crossref_title or "")

    return CrossrefVerification(
        doi=extracted.extracted_doi,
        crossref_title=crossref_title,
        crossref_authors=authors,
        journal=journal,
        year=year,
        match_score=score,
        is_confident_match=score >= TITLE_FUZZY_MATCH_THRESHOLD,
        publisher=record.get("publisher"),
        page_raw=record.get("page"),
        document_type=record.get("type"),
        language=record.get("language"),
    )
