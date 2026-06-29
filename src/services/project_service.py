from config import PDF_DIR, WAREHOUSE_DB_PATH
from database.connection import get_connection
from repository.project_repository import ProjectRepository


class ProjectService:
    def get_or_create_default(self) -> int:
        with get_connection(WAREHOUSE_DB_PATH) as conn:
            return ProjectRepository(conn).get_or_create_default(str(PDF_DIR))

    def list_projects(self) -> list[dict]:
        with get_connection(WAREHOUSE_DB_PATH) as conn:
            return [dict(row) for row in ProjectRepository(conn).list_projects()]

    def create(self, name: str) -> int:
        with get_connection(WAREHOUSE_DB_PATH) as conn:
            return ProjectRepository(conn).create(name)

    def rename(self, project_id: int, new_name: str) -> None:
        with get_connection(WAREHOUSE_DB_PATH) as conn:
            ProjectRepository(conn).rename(project_id, new_name)

    def delete(self, project_id: int) -> None:
        with get_connection(WAREHOUSE_DB_PATH) as conn:
            ProjectRepository(conn).delete(project_id)
