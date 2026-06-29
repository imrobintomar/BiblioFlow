import sqlite3
from collections import Counter
from itertools import combinations

from engine.clustering import local_citation_edges
from engine.network_utils import build_graph


def reference_cocitation_edges(conn: sqlite3.Connection, project_id: int) -> list[tuple[str, str, int]]:
    """Two references are co-cited if the same citing paper (within this
    corpus) lists both in its reference list. Works regardless of whether
    the references resolved to a DOI, since co-citation only needs
    co-occurrence within one citing paper's reference list, not matching
    across papers (unlike bibliographic coupling)."""
    rows = conn.execute(
        """
        SELECT paper_references.paper_id AS paper_id,
               COALESCE(reference_entries.doi, reference_entries.raw_text) AS ref_label
        FROM paper_references
        JOIN reference_entries ON reference_entries.id = paper_references.reference_id
        JOIN papers ON papers.id = paper_references.paper_id
        WHERE papers.project_id = ? AND COALESCE(reference_entries.doi, reference_entries.raw_text) IS NOT NULL
        """,
        (project_id,),
    ).fetchall()

    by_paper: dict[int, set[str]] = {}
    for r in rows:
        label = r["ref_label"]
        # OpenAlex work IDs are long URLs; truncate for a readable node label.
        if label and label.startswith("http"):
            label = label.rsplit("/", 1)[-1]
        by_paper.setdefault(r["paper_id"], set()).add(label)

    edge_counts: Counter = Counter()
    for refs in by_paper.values():
        for a, b in combinations(sorted(refs), 2):
            edge_counts[(a, b)] += 1

    return [(a, b, w) for (a, b), w in edge_counts.items()]


def reference_cocitation_network(conn: sqlite3.Connection, project_id: int):
    edges = reference_cocitation_edges(conn, project_id)
    return build_graph(edges, directed=False), edges


def historiograph(conn: sqlite3.Connection, project_id: int) -> dict:
    """Chronological citation tree: local citing->cited edges (within this
    corpus) annotated with each paper's publication year, for a historiograph-
    style chronological layout. Author/Journal co-citation networks are not
    implemented -- they require resolving each REFERENCED work's own authors/
    journal via an extra API call per reference (potentially hundreds per
    paper), which this milestone doesn't perform."""
    edges = local_citation_edges(conn, project_id)
    years = {
        r["title"]: r["year"]
        for r in conn.execute(
            "SELECT title, year FROM papers WHERE project_id = ?", (project_id,)
        ).fetchall()
    }
    nodes = sorted({n for e in edges for n in (e[0], e[1])}, key=lambda n: years.get(n) or 0)
    return {
        "edges": [{"citing": a, "cited": b} for a, b, _ in edges],
        "nodes_by_year": [{"title": n, "year": years.get(n)} for n in nodes],
        "note": "Local citation links only (within this imported corpus, matched by "
        "DOI) -- expected to be sparse/empty for small or topically diverse corpora.",
    }
