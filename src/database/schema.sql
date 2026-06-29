CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    pdf_dir TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS publishers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS countries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS institutions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    country_id INTEGER REFERENCES countries(id)
);

CREATE TABLE IF NOT EXISTS journals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    publisher_id INTEGER REFERENCES publishers(id)
);

CREATE TABLE IF NOT EXISTS authors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS reference_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doi TEXT UNIQUE,
    raw_text TEXT
);

CREATE TABLE IF NOT EXISTS funders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS paper_funders (
    paper_id INTEGER NOT NULL REFERENCES papers(id),
    funder_id INTEGER NOT NULL REFERENCES funders(id),
    grant_id TEXT,
    PRIMARY KEY (paper_id, funder_id, grant_id)
);

CREATE TABLE IF NOT EXISTS papers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    filename TEXT NOT NULL,
    checksum TEXT,
    doi TEXT,
    title TEXT,
    abstract TEXT,
    journal_id INTEGER REFERENCES journals(id),
    publisher_id INTEGER REFERENCES publishers(id),
    year INTEGER,
    publication_date TEXT,
    document_type TEXT,
    language TEXT,
    open_access INTEGER,
    cited_by_count INTEGER,
    eid TEXT,
    pmid TEXT,
    semantic_scholar_id TEXT,
    trial_ids TEXT,
    ethics_statement TEXT,
    consent_statement TEXT,
    funding_text_raw TEXT,
    sections_json TEXT,
    oa_url TEXT,
    oa_status TEXT,
    license TEXT,
    table_count INTEGER,
    figure_count INTEGER,
    pages_raw TEXT,
    page_count INTEGER,
    word_count INTEGER,
    status TEXT NOT NULL,
    error TEXT,
    source TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (project_id, filename)
);

CREATE TABLE IF NOT EXISTS paper_authors (
    paper_id INTEGER NOT NULL REFERENCES papers(id),
    author_id INTEGER NOT NULL REFERENCES authors(id),
    author_order INTEGER,
    PRIMARY KEY (paper_id, author_id)
);

CREATE TABLE IF NOT EXISTS paper_institutions (
    paper_id INTEGER NOT NULL REFERENCES papers(id),
    institution_id INTEGER NOT NULL REFERENCES institutions(id),
    PRIMARY KEY (paper_id, institution_id)
);

CREATE TABLE IF NOT EXISTS paper_keywords (
    paper_id INTEGER NOT NULL REFERENCES papers(id),
    keyword_id INTEGER NOT NULL REFERENCES keywords(id),
    PRIMARY KEY (paper_id, keyword_id)
);

CREATE TABLE IF NOT EXISTS paper_references (
    paper_id INTEGER NOT NULL REFERENCES papers(id),
    reference_id INTEGER NOT NULL REFERENCES reference_entries(id),
    PRIMARY KEY (paper_id, reference_id)
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER REFERENCES projects(id),
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    type TEXT NOT NULL,
    status TEXT NOT NULL,
    message TEXT,
    duration_ms INTEGER
);

CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER REFERENCES projects(id),
    type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    progress REAL NOT NULL DEFAULT 0,
    message TEXT,
    started_at TEXT,
    finished_at TEXT
);

CREATE TABLE IF NOT EXISTS analysis_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER REFERENCES projects(id),
    module TEXT NOT NULL,
    metrics_json TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS field_provenance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id INTEGER NOT NULL REFERENCES papers(id),
    field_name TEXT NOT NULL,
    source TEXT NOT NULL,
    method TEXT,
    confidence REAL,
    extracted_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (paper_id, field_name)
);

CREATE TABLE IF NOT EXISTS exports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER REFERENCES projects(id),
    kind TEXT NOT NULL,
    path TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_papers_project ON papers(project_id);
CREATE INDEX IF NOT EXISTS idx_papers_doi ON papers(doi);
CREATE INDEX IF NOT EXISTS idx_events_project ON events(project_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_jobs_project ON jobs(project_id, status);
