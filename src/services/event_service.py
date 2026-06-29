from config import WAREHOUSE_DB_PATH
from database.connection import get_connection
from repository.event_repository import EventRepository


class EventService:
    def log(self, project_id, event_type: str, status: str, message: str = "", duration_ms=None):
        with get_connection(WAREHOUSE_DB_PATH) as conn:
            EventRepository(conn).log(project_id, event_type, status, message, duration_ms)

    def recent(self, project_id=None, limit: int = 20) -> list[dict]:
        with get_connection(WAREHOUSE_DB_PATH) as conn:
            return [dict(row) for row in EventRepository(conn).recent(project_id, limit)]
