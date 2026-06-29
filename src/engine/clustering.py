import sqlite3
from collections import Counter
from itertools import combinations

from engine.network_utils import build_graph


def _pairwise_edges(conn: sqlite3.Connection, query: str, params: tuple, group_col: str, item_col: str) -> list[tuple[str, str, int]]:
    """Generic co-occurrence builder: groups rows by group_col, then emits
    one edge per unordered pair of distinct item_col values within a group
    (e.g. co-authors on the same paper, co-keywords on the same paper)."""
    rows = conn.execute(query, params).fetchall()
    by_group: dict[int, set[str]] = {}
    for r in rows:
        by_group.setdefault(r[group_col], set()).add(r[item_col])

    edge_counts: Counter = Counter()
    for items in by_group.values():
        for a, b in combinations(sorted(items), 2):
            edge_counts[(a, b)] += 1

    return [(a, b, w) for (a, b), w in edge_counts.items()]


def co_authorship_edges(conn: sqlite3.Connection, project_id: int) -> list[tuple[str, str, int]]:
    return _pairwise_edges(
        conn,
        """
        SELECT paper_authors.paper_id AS paper_id, authors.full_name AS author
        FROM paper_authors
        JOIN authors ON authors.id = paper_authors.author_id
        JOIN papers ON papers.id = paper_authors.paper_id
        WHERE papers.project_id = ?
        """,
        (project_id,),
        "paper_id",
        "author",
    )


def keyword_cooccurrence_edges(conn: sqlite3.Connection, project_id: int) -> list[tuple[str, str, int]]:
    return _pairwise_edges(
        conn,
        """
        SELECT paper_keywords.paper_id AS paper_id, keywords.term AS keyword
        FROM paper_keywords
        JOIN keywords ON keywords.id = paper_keywords.keyword_id
        JOIN papers ON papers.id = paper_keywords.paper_id
        WHERE papers.project_id = ?
        """,
        (project_id,),
        "paper_id",
        "keyword",
    )


def bibliographic_coupling_edges(conn: sqlite3.Connection, project_id: int) -> list[tuple[str, str, int]]:
    """Two papers are 'coupled' if they cite at least one shared reference.
    Coupling strength = number of shared reference entries."""
    rows = conn.execute(
        """
        SELECT papers.title AS title, paper_references.reference_id AS reference_id
        FROM paper_references
        JOIN papers ON papers.id = paper_references.paper_id
        WHERE papers.project_id = ?
        """,
        (project_id,),
    ).fetchall()

    refs_by_paper: dict[str, set[int]] = {}
    for r in rows:
        refs_by_paper.setdefault(r["title"] or "Untitled", set()).add(r["reference_id"])

    edge_counts: Counter = Counter()
    for (p1, refs1), (p2, refs2) in combinations(refs_by_paper.items(), 2):
        shared = len(refs1 & refs2)
        if shared > 0:
            edge_counts[(p1, p2)] = shared

    return [(a, b, w) for (a, b), w in edge_counts.items()]


def local_citation_edges(conn: sqlite3.Connection, project_id: int) -> list[tuple[str, str, int]]:
    """Directed citing -> cited edges within this corpus only, matched by DOI."""
    rows = conn.execute(
        """
        SELECT citing.title AS citing_title, cited.title AS cited_title
        FROM papers AS citing
        JOIN paper_references ON paper_references.paper_id = citing.id
        JOIN reference_entries ON reference_entries.id = paper_references.reference_id
        JOIN papers AS cited ON cited.doi = reference_entries.doi
        WHERE citing.project_id = ? AND cited.project_id = ? AND reference_entries.doi IS NOT NULL
        """,
        (project_id, project_id),
    ).fetchall()
    return [(r["citing_title"] or "Untitled", r["cited_title"] or "Untitled", 1) for r in rows]


def build_network(conn: sqlite3.Connection, project_id: int, network_type: str):
    builders = {
        "co_authorship": (co_authorship_edges, False),
        "keyword_cooccurrence": (keyword_cooccurrence_edges, False),
        "bibliographic_coupling": (bibliographic_coupling_edges, False),
        "citation": (local_citation_edges, True),
    }
    builder, directed = builders[network_type]
    edges = builder(conn, project_id)
    return build_graph(edges, directed=directed), edges
