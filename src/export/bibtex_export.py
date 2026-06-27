import re
from pathlib import Path

from models import PipelineRecord


def _bibtex_key(record: PipelineRecord) -> str:
    base = record.scopus.doi if record.scopus else record.filename
    return re.sub(r"[^A-Za-z0-9]", "_", base)


def export_bibtex(records: list[PipelineRecord], output_path: Path) -> None:
    entries = []
    for r in records:
        if not r.scopus:
            continue
        s = r.scopus
        authors = " and ".join(s.authors) if s.authors else ""
        entry = (
            f"@article{{{_bibtex_key(r)},\n"
            f"  title = {{{s.title or ''}}},\n"
            f"  author = {{{authors}}},\n"
            f"  journal = {{{s.source_title or ''}}},\n"
            f"  year = {{{(s.publication_date or '')[:4]}}},\n"
            f"  doi = {{{s.doi}}},\n"
            f"  keywords = {{{', '.join(s.keywords)}}},\n"
            f"  abstract = {{{s.abstract or ''}}}\n"
            f"}}"
        )
        entries.append(entry)

    output_path.write_text("\n\n".join(entries))
