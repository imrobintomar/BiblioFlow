from pathlib import Path

from extract import docling_extract, text_patterns
from extract.checksum import file_checksum
from extract.doi import extract_doi
from extract.title import extract_title
from models import ExtractedRecord


def extract_from_pdf(pdf_path: Path) -> ExtractedRecord:
    checksum = file_checksum(pdf_path)
    doi, source, occurrence_pages = extract_doi(pdf_path)
    title = extract_title(pdf_path)

    record = ExtractedRecord(
        filename=pdf_path.name,
        checksum=checksum,
        extracted_title=title,
        extracted_doi=doi,
        doi_source=source,
        doi_occurrence_pages=occurrence_pages,
    )

    try:
        doc = docling_extract.convert(pdf_path)
    except Exception:  # noqa: BLE001
        # Docling structural extraction is additive -- if it fails for a
        # given PDF, DOI/title (the load-bearing fields) are unaffected.
        return record

    full_text = " ".join(doc.sections.values())

    record.abstract = doc.abstract
    record.sections = doc.sections
    record.table_count = doc.table_count
    record.figure_count = doc.figure_count
    record.funding_text = doc.funding_text
    record.ethics_statement = doc.ethics_text
    record.references_text_raw = doc.references_text

    record.keywords = text_patterns.extract_keywords(full_text)
    record.trial_ids = text_patterns.extract_trial_ids(full_text)
    record.orcid_ids = text_patterns.extract_orcids(full_text)
    record.consent_statement = text_patterns.extract_consent_statement(full_text)
    record.grant_ids = text_patterns.extract_grant_ids(doc.funding_text or "")
    record.known_funders = text_patterns.extract_known_funders(doc.funding_text or full_text)

    return record
