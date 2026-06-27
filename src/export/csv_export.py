import csv
from pathlib import Path

from models import PipelineRecord

FIELDS = [
    "filename",
    "status",
    "doi",
    "title",
    "authors",
    "journal",
    "year",
    "cited_by_count",
    "keywords",
    "crossref_match_score",
]


def export_csv(records: list[PipelineRecord], output_path: Path) -> None:
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for r in records:
            scopus = r.scopus
            crossref = r.crossref
            writer.writerow(
                {
                    "filename": r.filename,
                    "status": r.status.value,
                    "doi": (scopus.doi if scopus else (crossref.doi if crossref else "")),
                    "title": (scopus.title if scopus and scopus.title else (crossref.crossref_title if crossref else "")),
                    "authors": "; ".join(scopus.authors) if scopus else "",
                    "journal": (scopus.source_title if scopus else (crossref.journal if crossref else "")),
                    "year": (scopus.publication_date if scopus else (crossref.year if crossref else "")),
                    "cited_by_count": scopus.cited_by_count if scopus else "",
                    "keywords": "; ".join(scopus.keywords) if scopus else "",
                    "crossref_match_score": crossref.match_score if crossref else "",
                }
            )
