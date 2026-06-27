import re
from collections import defaultdict
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF

DOI_REGEX = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", re.IGNORECASE)
REFERENCES_HEADING_REGEX = re.compile(
    r"^\s*(references|bibliography|works cited)\s*$", re.IGNORECASE
)
TRAILING_PUNCT = ".,;)]}"


def _clean_doi(raw: str) -> str:
    return raw.strip().rstrip(TRAILING_PUNCT)


def _doi_from_xmp_metadata(doc: "fitz.Document") -> Optional[str]:
    xml = doc.get_xml_metadata()
    if not xml:
        return None
    # prism:doi or dc:identifier tags used by most publisher XMP blocks.
    for pattern in (r"prism:doi>([^<]+)<", r"dc:identifier[^>]*>([^<]+)<"):
        match = re.search(pattern, xml, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            doi_match = DOI_REGEX.search(candidate)
            if doi_match:
                return _clean_doi(doi_match.group(0))
    return None


def _doi_from_docinfo(doc: "fitz.Document") -> Optional[str]:
    metadata = doc.metadata or {}
    for value in metadata.values():
        if not value:
            continue
        match = DOI_REGEX.search(value)
        if match:
            return _clean_doi(match.group(0))
    return None


def _find_references_page_index(pages_text: list[str]) -> Optional[int]:
    for idx, text in enumerate(pages_text):
        for line in text.splitlines():
            if REFERENCES_HEADING_REGEX.match(line):
                return idx
    return None


def extract_doi(pdf_path: Path) -> tuple[Optional[str], Optional[str], int]:
    """Returns (doi, source, occurrence_page_count).

    Priority: embedded metadata > DOI repeated across multiple pages
    (article's own DOI in header/footer) > position on page 1 (before
    the references section, to avoid grabbing a citation DOI).
    """
    doc = fitz.open(pdf_path)
    try:
        metadata_doi = _doi_from_xmp_metadata(doc) or _doi_from_docinfo(doc)
        if metadata_doi:
            return metadata_doi, "metadata", 0

        pages_text = [page.get_text() for page in doc]

        doi_pages: dict[str, set[int]] = defaultdict(set)
        for page_idx, text in enumerate(pages_text):
            for match in DOI_REGEX.finditer(text):
                doi_pages[_clean_doi(match.group(0))].add(page_idx)

        repeated = {d: pages for d, pages in doi_pages.items() if len(pages) > 1}
        if repeated:
            best_doi = max(repeated, key=lambda d: len(repeated[d]))
            return best_doi, "frequency", len(repeated[best_doi])

        if not pages_text:
            return None, None, 0

        references_idx = _find_references_page_index(pages_text)
        search_pages = pages_text[:2]
        if references_idx is not None and references_idx < 2:
            search_pages = pages_text[:references_idx] or pages_text[:1]

        for text in search_pages:
            match = DOI_REGEX.search(text)
            if match:
                return _clean_doi(match.group(0)), "position", 1

        return None, None, 0
    finally:
        doc.close()
