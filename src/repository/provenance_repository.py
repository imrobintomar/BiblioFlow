import sqlite3


class ProvenanceRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def record(
        self,
        paper_id: int,
        field_name: str,
        source: str,
        method: str = "",
        confidence: float = 1.0,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO field_provenance (paper_id, field_name, source, method, confidence, extracted_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(paper_id, field_name) DO UPDATE SET
                source = excluded.source,
                method = excluded.method,
                confidence = excluded.confidence,
                extracted_at = excluded.extracted_at
            """,
            (paper_id, field_name, source, method, confidence),
        )

    def for_paper(self, paper_id: int) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM field_provenance WHERE paper_id = ? ORDER BY field_name",
            (paper_id,),
        ).fetchall()
