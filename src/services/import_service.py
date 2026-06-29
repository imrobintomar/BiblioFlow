import threading
from pathlib import Path

from config import PDF_DIR, WAREHOUSE_DB_PATH
from database.connection import get_connection
from db import get_connection as get_legacy_connection
from db import upsert_state
from repository.job_repository import JobRepository
from repository.paper_repository import PaperRepository
from services.enrichment_service import EnrichmentService
from services.event_service import EventService
from services.project_service import ProjectService


class ImportService:
    """Runs the (unmodified) extraction pipeline in a background thread and
    persists its output into the normalized warehouse DB, with job/event
    tracking the UI can poll. No queue/worker process -- a single background
    thread is enough for a single-user local app; the public interface
    (start_import -> job_id, get_job) is what would change if a real queue
    is introduced later."""

    def __init__(self):
        self.events = EventService()
        self.projects = ProjectService()
        self.enrichment = EnrichmentService()

    def start_import(self, pdf_dir: Path = PDF_DIR, force: bool = False) -> int:
        project_id = self.projects.get_or_create_default()
        with get_connection(WAREHOUSE_DB_PATH) as conn:
            job_id = JobRepository(conn).create(project_id, "import")

        thread = threading.Thread(
            target=self._run, args=(job_id, project_id, pdf_dir, force), daemon=True
        )
        thread.start()
        return job_id

    def _run(self, job_id: int, project_id: int, pdf_dir: Path, force: bool) -> None:
        from pipeline import process_pdf

        self.events.log(project_id, "import", "started", f"Importing from {pdf_dir}")

        pdf_files = sorted(pdf_dir.glob("*.pdf")) if pdf_dir.exists() else []
        total = len(pdf_files) or 1

        try:
            with get_connection(WAREHOUSE_DB_PATH) as warehouse_conn:
                jobs = JobRepository(warehouse_conn)
                papers = PaperRepository(warehouse_conn)

                with get_legacy_connection() as legacy_conn:
                    for idx, pdf_path in enumerate(pdf_files, start=1):
                        record = process_pdf(pdf_path, legacy_conn, force, fetch_scopus=True)
                        upsert_state(
                            legacy_conn,
                            filename=record.filename,
                            checksum=record.checksum,
                            status=record.status.value,
                            doi=record.extracted.extracted_doi if record.extracted else None,
                            error=record.error,
                            record_json=record.model_dump_json(),
                        )
                        paper_id = papers.upsert_from_pipeline_record(project_id, record)
                        warehouse_conn.commit()

                        doi = record.extracted.extracted_doi if record.extracted else None
                        if doi:
                            jobs.update_progress(job_id, idx / total, f"Enriching {record.filename}")
                            try:
                                self.enrichment.enrich_paper(warehouse_conn, paper_id, doi)
                                warehouse_conn.commit()
                            except Exception as exc:  # noqa: BLE001
                                self.events.log(
                                    project_id, "enrichment", "failed", f"{record.filename}: {exc}"
                                )

                        jobs.update_progress(job_id, idx / total, f"Processed {record.filename}")
                        self.events.log(
                            project_id, "paper_processed", record.status.value, record.filename
                        )

                    self.enrichment.backfill_institution_countries(warehouse_conn)
                    warehouse_conn.commit()

                jobs.finish(job_id, "done", f"Processed {len(pdf_files)} PDF(s)")
            self.events.log(project_id, "import", "finished", f"Processed {len(pdf_files)} PDF(s)")
        except Exception as exc:  # noqa: BLE001
            with get_connection(WAREHOUSE_DB_PATH) as warehouse_conn:
                JobRepository(warehouse_conn).finish(job_id, "failed", str(exc))
            self.events.log(project_id, "import", "failed", str(exc))

    def get_job(self, job_id: int) -> dict | None:
        with get_connection(WAREHOUSE_DB_PATH) as conn:
            row = JobRepository(conn).get(job_id)
            return dict(row) if row else None
