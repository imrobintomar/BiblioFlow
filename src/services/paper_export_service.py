import json

from config import WAREHOUSE_DB_PATH
from database.connection import get_connection
from repository.paper_repository import PaperRepository
from repository.project_repository import ProjectRepository
from utils.export_utils import rows_to_csv, rows_to_excel_bytes

LIBRARY_COLUMNS = [
    "title",
    "doi",
    "journal_name",
    "year",
    "cited_by_count",
    "status",
    "authors",
]


class PaperExportService:
    def _project_id(self, conn) -> int:
        return ProjectRepository(conn).get_or_create_default("")

    def _library_rows(self) -> list[dict]:
        with get_connection(WAREHOUSE_DB_PATH) as conn:
            project_id = self._project_id(conn)
            papers = PaperRepository(conn).list_papers(project_id)
        for p in papers:
            p["authors"] = "; ".join(p.get("authors", []))
        return papers

    def library_csv(self) -> str:
        return rows_to_csv(self._library_rows(), LIBRARY_COLUMNS)

    def library_excel(self) -> bytes:
        return rows_to_excel_bytes(self._library_rows(), LIBRARY_COLUMNS)

    def paper_json(self, paper_id: int) -> str:
        with get_connection(WAREHOUSE_DB_PATH) as conn:
            paper = PaperRepository(conn).get_paper(paper_id)
        return json.dumps(paper, indent=2, default=str)
