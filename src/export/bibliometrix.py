import csv
from pathlib import Path

from models import PipelineRecord

# Column headers matching a standard Scopus CSV export, so the file loads
# directly into R's bibliometrix::convert2df(dbsource="scopus", format="csv").
BIBLIOMETRIX_FIELDS = [
    "Authors",
    "Author full names",
    "Title",
    "Year",
    "Source title",
    "Cited by",
    "DOI",
    "Affiliations",
    "Abstract",
    "Author Keywords",
    "References",
    "Document Type",
    "Language of Original Document",
    "EID",
    "Source",
]


def export_bibliometrix_csv(records: list[PipelineRecord], output_path: Path) -> None:
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=BIBLIOMETRIX_FIELDS)
        writer.writeheader()
        for r in records:
            if not r.scopus:
                continue
            s = r.scopus
            year = (s.publication_date or "")[:4]
            writer.writerow(
                {
                    "Authors": "; ".join(s.authors),
                    "Author full names": "; ".join(s.authors),
                    "Title": s.title or "",
                    "Year": year,
                    "Source title": s.source_title or "",
                    "Cited by": s.cited_by_count or 0,
                    "DOI": s.doi,
                    "Affiliations": "; ".join(s.affiliations),
                    "Abstract": s.abstract or "",
                    "Author Keywords": "; ".join(s.keywords),
                    "References": "; ".join(s.references),
                    "Document Type": "Article",
                    "Language of Original Document": "English",
                    "EID": s.eid or "",
                    "Source": "Scopus",
                }
            )
