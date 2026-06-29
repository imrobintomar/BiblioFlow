import json
import re
import sqlite3

from repository.lookup_repository import LookupRepository

_PAGE_RANGE_REGEX = re.compile(r"(\d+)\s*-\s*(\d+)")


def _parse_page_count(pages_raw: str | None) -> int | None:
    if not pages_raw:
        return None
    match = _PAGE_RANGE_REGEX.search(pages_raw)
    if not match:
        return None
    start, end = int(match.group(1)), int(match.group(2))
    return end - start + 1 if end >= start else None


class PaperRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.authors = LookupRepository(conn, "authors", "full_name")
        self.journals = LookupRepository(conn, "journals")
        self.institutions = LookupRepository(conn, "institutions")
        self.publishers = LookupRepository(conn, "publishers")
        self.countries = LookupRepository(conn, "countries")
        self.keywords = LookupRepository(conn, "keywords", "term")
        self.funders = LookupRepository(conn, "funders")

    def upsert_from_pipeline_record(self, project_id: int, record) -> int:
        """Persists a models.PipelineRecord (extraction pipeline output) into
        the normalized warehouse schema. Read-only consumer of the pipeline's
        output -- does not touch the extraction/verify/scopus code at all."""
        extracted = record.extracted
        crossref = record.crossref
        scopus = record.scopus

        doi = extracted.extracted_doi if extracted else None
        title = (scopus.title if scopus else None) or (
            crossref.crossref_title if crossref else None
        ) or (extracted.extracted_title if extracted else None)
        journal_name = (scopus.source_title if scopus else None) or (
            crossref.journal if crossref else None
        )
        year = None
        publication_date = scopus.publication_date if scopus else None
        if publication_date:
            year = int(publication_date[:4]) if publication_date[:4].isdigit() else None
        elif crossref and crossref.year:
            year = crossref.year

        journal_id = self.journals.get_or_create(journal_name) if journal_name else None
        cited_by_count = scopus.cited_by_count if scopus else None
        eid = scopus.eid if scopus else None
        source = "scopus" if scopus else ("crossref" if crossref else "extracted")

        abstract = (scopus.abstract if scopus else None) or (extracted.abstract if extracted else None)
        trial_ids = json.dumps(extracted.trial_ids) if extracted and extracted.trial_ids else None
        ethics_statement = extracted.ethics_statement if extracted else None
        consent_statement = extracted.consent_statement if extracted else None
        funding_text_raw = extracted.funding_text if extracted else None
        sections_json = json.dumps(extracted.sections) if extracted and extracted.sections else None
        table_count = extracted.table_count if extracted else None
        figure_count = extracted.figure_count if extracted else None

        publisher_name = crossref.publisher if crossref else None
        publisher_id = self.publishers.get_or_create(publisher_name) if publisher_name else None
        document_type = crossref.document_type if crossref else None
        language = crossref.language if crossref else None
        pages_raw = crossref.page_raw if crossref else None
        page_count = _parse_page_count(pages_raw)
        word_count = (
            sum(len(text.split()) for text in extracted.sections.values())
            if extracted and extracted.sections
            else None
        )

        existing = self.conn.execute(
            "SELECT id FROM papers WHERE project_id = ? AND filename = ?",
            (project_id, record.filename),
        ).fetchone()

        update_values = (
            record.checksum,
            doi,
            title,
            abstract,
            journal_id,
            publisher_id,
            year,
            publication_date,
            cited_by_count,
            eid,
            trial_ids,
            ethics_statement,
            consent_statement,
            funding_text_raw,
            sections_json,
            table_count,
            figure_count,
            document_type,
            language,
            pages_raw,
            page_count,
            word_count,
            record.status.value,
            record.error,
            source,
        )

        if existing:
            paper_id = existing["id"]
            self.conn.execute(
                """
                UPDATE papers SET checksum=?, doi=?, title=?, abstract=?, journal_id=?, publisher_id=?,
                    year=?, publication_date=?, cited_by_count=?, eid=?, trial_ids=?, ethics_statement=?,
                    consent_statement=?, funding_text_raw=?, sections_json=?, table_count=?,
                    figure_count=?, document_type=?, language=?, pages_raw=?, page_count=?, word_count=?,
                    status=?, error=?, source=?, updated_at=datetime('now')
                WHERE id=?
                """,
                update_values + (paper_id,),
            )
        else:
            cur = self.conn.execute(
                """
                INSERT INTO papers (project_id, filename, checksum, doi, title, abstract,
                    journal_id, publisher_id, year, publication_date, cited_by_count, eid, trial_ids,
                    ethics_statement, consent_statement, funding_text_raw, sections_json,
                    table_count, figure_count, document_type, language, pages_raw, page_count,
                    word_count, status, error, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (project_id, record.filename) + update_values,
            )
            paper_id = cur.lastrowid

        self._sync_authors(paper_id, record)
        self._sync_institutions(paper_id, scopus)
        if extracted and extracted.keywords:
            self.add_keywords(paper_id, extracted.keywords)
        if extracted and extracted.known_funders:
            self.add_funders(
                paper_id, [{"name": f, "grant_id": None} for f in extracted.known_funders]
            )
        return paper_id

    def _sync_authors(self, paper_id: int, record) -> None:
        self.conn.execute("DELETE FROM paper_authors WHERE paper_id = ?", (paper_id,))
        authors = []
        if record.crossref and record.crossref.crossref_authors:
            authors = record.crossref.crossref_authors
        elif record.scopus and record.scopus.authors:
            authors = record.scopus.authors

        for order, name in enumerate(a for a in authors if a and a.strip()):
            author_id = self.authors.get_or_create(name)
            self.conn.execute(
                "INSERT OR IGNORE INTO paper_authors (paper_id, author_id, author_order) "
                "VALUES (?, ?, ?)",
                (paper_id, author_id, order),
            )

    def _sync_institutions(self, paper_id: int, scopus) -> None:
        self.conn.execute("DELETE FROM paper_institutions WHERE paper_id = ?", (paper_id,))
        if not scopus or not scopus.affiliations:
            return
        for name in scopus.affiliations:
            if not name or not name.strip():
                continue
            institution_id = self.institutions.get_or_create(name)
            self.conn.execute(
                "INSERT OR IGNORE INTO paper_institutions (paper_id, institution_id) VALUES (?, ?)",
                (paper_id, institution_id),
            )

    def list_papers(self, project_id: int) -> list[dict]:
        rows = self.conn.execute(
            """
            SELECT papers.*, journals.name AS journal_name
            FROM papers
            LEFT JOIN journals ON journals.id = papers.journal_id
            WHERE papers.project_id = ?
            ORDER BY papers.updated_at DESC
            """,
            (project_id,),
        ).fetchall()
        return [self._with_authors(dict(row)) for row in rows]

    def _with_authors(self, paper: dict) -> dict:
        authors = self.conn.execute(
            """
            SELECT authors.full_name FROM paper_authors
            JOIN authors ON authors.id = paper_authors.author_id
            WHERE paper_authors.paper_id = ?
            ORDER BY paper_authors.author_order
            """,
            (paper["id"],),
        ).fetchall()
        paper["authors"] = [a["full_name"] for a in authors]
        return paper

    def get_paper(self, paper_id: int) -> dict | None:
        row = self.conn.execute(
            """
            SELECT papers.*, journals.name AS journal_name
            FROM papers LEFT JOIN journals ON journals.id = papers.journal_id
            WHERE papers.id = ?
            """,
            (paper_id,),
        ).fetchone()
        if not row:
            return None
        paper = self._with_authors(dict(row))
        paper["institutions"] = [
            r["name"]
            for r in self.conn.execute(
                """
                SELECT institutions.name FROM paper_institutions
                JOIN institutions ON institutions.id = paper_institutions.institution_id
                WHERE paper_institutions.paper_id = ?
                """,
                (paper_id,),
            ).fetchall()
        ]
        return paper

    def get_field(self, paper_id: int, field: str):
        row = self.conn.execute(f"SELECT {field} FROM papers WHERE id = ?", (paper_id,)).fetchone()
        return row[field] if row else None

    def update_fields_if_empty(self, paper_id: int, **fields) -> None:
        """Waterfall semantics: only write a field if it's currently NULL,
        so an earlier (higher-priority) source's value is never clobbered."""
        for field, value in fields.items():
            if value is None:
                continue
            current = self.get_field(paper_id, field)
            if current is None or current == "":
                self.conn.execute(f"UPDATE papers SET {field} = ? WHERE id = ?", (value, paper_id))

    def add_keywords(self, paper_id: int, terms: list[str]) -> None:
        for term in terms:
            if not term or not term.strip():
                continue
            keyword_id = self.keywords.get_or_create(term.strip())
            self.conn.execute(
                "INSERT OR IGNORE INTO paper_keywords (paper_id, keyword_id) VALUES (?, ?)",
                (paper_id, keyword_id),
            )

    def add_institutions_with_country(self, paper_id: int, institutions: list[dict]) -> None:
        """institutions: [{'name': str, 'country': str|None}, ...]"""
        for inst in institutions:
            name = inst.get("name")
            if not name or not name.strip():
                continue
            country_id = None
            if inst.get("country"):
                country_id = self.countries.get_or_create(inst["country"])
            institution_id = self.institutions.get_or_create(name, country_id=country_id)
            if country_id and institution_id:
                # Backfill country on institutions created earlier without one.
                self.conn.execute(
                    "UPDATE institutions SET country_id = ? WHERE id = ? AND country_id IS NULL",
                    (country_id, institution_id),
                )
            self.conn.execute(
                "INSERT OR IGNORE INTO paper_institutions (paper_id, institution_id) VALUES (?, ?)",
                (paper_id, institution_id),
            )

    def add_funders(self, paper_id: int, funders: list[dict]) -> None:
        """funders: [{'name': str, 'grant_id': str|None}, ...]"""
        for funder in funders:
            name = funder.get("name")
            if not name or not name.strip():
                continue
            funder_id = self.funders.get_or_create(name.strip())
            self.conn.execute(
                "INSERT OR IGNORE INTO paper_funders (paper_id, funder_id, grant_id) VALUES (?, ?, ?)",
                (paper_id, funder_id, funder.get("grant_id")),
            )

    def add_references(self, paper_id: int, references: list[dict]) -> None:
        """references: [{'doi': str|None, 'raw_text': str|None}, ...]"""
        for ref in references:
            doi, raw_text = ref.get("doi"), ref.get("raw_text")
            if not doi and not raw_text:
                continue
            if doi:
                row = self.conn.execute(
                    "SELECT id FROM reference_entries WHERE doi = ?", (doi,)
                ).fetchone()
                if row:
                    reference_id = row["id"]
                else:
                    cur = self.conn.execute(
                        "INSERT INTO reference_entries (doi, raw_text) VALUES (?, ?)",
                        (doi, raw_text),
                    )
                    reference_id = cur.lastrowid
            else:
                cur = self.conn.execute(
                    "INSERT INTO reference_entries (doi, raw_text) VALUES (NULL, ?)", (raw_text,)
                )
                reference_id = cur.lastrowid
            self.conn.execute(
                "INSERT OR IGNORE INTO paper_references (paper_id, reference_id) VALUES (?, ?)",
                (paper_id, reference_id),
            )

    def count(self, project_id: int) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) AS c FROM papers WHERE project_id = ?", (project_id,)
        ).fetchone()
        return row["c"]
