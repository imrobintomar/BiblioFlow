"""In-memory cache so each rendered chart/table panel can offer a CSV
download without a dedicated Flask route per metric. Single-process,
single-user local app -- a module-level dict is sufficient; this would need
to move to a real cache/session store if BiblioFlow ever serves multiple
concurrent users."""

_CACHE: dict[str, tuple[list[str], list[dict]]] = {}


def register(panel_id: str, columns: list[str], rows: list[dict]) -> None:
    _CACHE[panel_id] = (columns, rows)


def get(panel_id: str) -> tuple[list[str], list[dict]] | None:
    return _CACHE.get(panel_id)
