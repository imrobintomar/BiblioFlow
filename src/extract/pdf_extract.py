from pathlib import Path

from extract.checksum import file_checksum
from extract.doi import extract_doi
from extract.title import extract_title
from models import ExtractedRecord


def extract_from_pdf(pdf_path: Path) -> ExtractedRecord:
    checksum = file_checksum(pdf_path)
    doi, source, occurrence_pages = extract_doi(pdf_path)
    title = extract_title(pdf_path)

    return ExtractedRecord(
        filename=pdf_path.name,
        checksum=checksum,
        extracted_title=title,
        extracted_doi=doi,
        doi_source=source,
        doi_occurrence_pages=occurrence_pages,
    )
