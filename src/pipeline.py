import argparse
import logging
from pathlib import Path

from config import EXPORT_DIR, LOGS_DIR, PDF_DIR
from db import get_connection, get_state, upsert_state
from export.bibliometrix import export_bibliometrix_csv
from export.bibtex_export import export_bibtex
from export.csv_export import export_csv
from export.json_export import export_json
from extract.checksum import file_checksum
from extract.pdf_extract import extract_from_pdf
from models import PipelineRecord, PipelineStatus
from scopus.fetch import fetch_scopus_record
from verify.validation import verify_doi

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "pipeline.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("pipeline")


def process_pdf(pdf_path: Path, conn, force: bool, fetch_scopus: bool) -> PipelineRecord:
    checksum = file_checksum(pdf_path)
    existing = get_state(conn, pdf_path.name)

    if existing and existing["checksum"] == checksum and not force:
        logger.info("Skipping %s (already processed, status=%s)", pdf_path.name, existing["status"])
        return PipelineRecord.model_validate_json(existing["record_json"])

    record = PipelineRecord(filename=pdf_path.name, checksum=checksum)

    try:
        extracted = extract_from_pdf(pdf_path)
        record.extracted = extracted
        record.status = PipelineStatus.EXTRACTED if extracted.extracted_doi else PipelineStatus.EXTRACT_FAILED
        logger.info(
            "%s -> DOI=%s (source=%s)", pdf_path.name, extracted.extracted_doi, extracted.doi_source
        )

        if not extracted.extracted_doi:
            record.error = "No DOI found in PDF"
            return record

        crossref = verify_doi(extracted)
        record.crossref = crossref

        if crossref is None:
            record.status = PipelineStatus.VERIFY_FAILED
            record.error = "DOI not found on CrossRef"
            return record

        if not crossref.is_confident_match:
            record.status = PipelineStatus.NEEDS_REVIEW
            record.error = f"Low title match confidence ({crossref.match_score:.0f})"
            return record

        record.status = PipelineStatus.VERIFIED

        if fetch_scopus:
            scopus_record = fetch_scopus_record(extracted.extracted_doi)
            if scopus_record:
                record.scopus = scopus_record
                record.status = PipelineStatus.SCOPUS_FETCHED
            else:
                record.status = PipelineStatus.SCOPUS_FAILED
                record.error = "DOI not found on Scopus"

    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed processing %s", pdf_path.name)
        record.status = PipelineStatus.EXTRACT_FAILED
        record.error = str(exc)

    return record


def run_pipeline(pdf_dir: Path, force: bool, fetch_scopus: bool) -> list[PipelineRecord]:
    pdf_files = sorted(pdf_dir.glob("*.pdf"))
    records: list[PipelineRecord] = []

    with get_connection() as conn:
        for pdf_path in pdf_files:
            record = process_pdf(pdf_path, conn, force, fetch_scopus)
            records.append(record)
            upsert_state(
                conn,
                filename=record.filename,
                checksum=record.checksum,
                status=record.status.value,
                doi=record.extracted.extracted_doi if record.extracted else None,
                error=record.error,
                record_json=record.model_dump_json(),
            )

    return records


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="BiblioFlow", description="BiblioFlow: PDF -> DOI -> CrossRef -> Scopus bibliometric pipeline"
    )
    parser.add_argument("--input", type=Path, default=PDF_DIR, help="Folder of PDFs")
    parser.add_argument("--output", type=Path, default=EXPORT_DIR, help="Output folder")
    parser.add_argument("--force", action="store_true", help="Reprocess even if unchanged")
    parser.add_argument("--no-scopus", action="store_true", help="Skip Scopus fetch stage")
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)

    records = run_pipeline(args.input, force=args.force, fetch_scopus=not args.no_scopus)

    needs_review = [r for r in records if r.status == PipelineStatus.NEEDS_REVIEW]
    if needs_review:
        export_csv(needs_review, args.output / "needs_review.csv")
        logger.warning("%d records flagged for manual review", len(needs_review))

    export_json(records, args.output / "results.json")
    export_csv(records, args.output / "results.csv")
    export_bibtex(records, args.output / "results.bib")
    export_bibliometrix_csv(records, args.output / "scopus_bibliometrix_export.csv")

    logger.info("Done. %d PDFs processed -> %s", len(records), args.output)


if __name__ == "__main__":
    main()
