"""One-off migration: reads the existing pipeline_state table (legacy
extraction-pipeline cache) and populates the normalized warehouse DB.
Does not touch the legacy database.sqlite or any extraction code."""

from config import PDF_DIR, WAREHOUSE_DB_PATH
from data_loader import load_all_records
from database.connection import get_connection
from repository.paper_repository import PaperRepository
from repository.project_repository import ProjectRepository


def main() -> None:
    records = load_all_records()
    print(f"Found {len(records)} record(s) in legacy pipeline_state.")

    with get_connection(WAREHOUSE_DB_PATH) as conn:
        project_id = ProjectRepository(conn).get_or_create_default(str(PDF_DIR))
        papers = PaperRepository(conn)
        for record in records:
            paper_id = papers.upsert_from_pipeline_record(project_id, record)
            print(f"  upserted paper id={paper_id} ({record.filename})")

    print(f"Done. Warehouse DB: {WAREHOUSE_DB_PATH}")


if __name__ == "__main__":
    main()
