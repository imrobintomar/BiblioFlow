# BiblioFlow

A bibliometric analysis platform that takes downloaded PDFs and turns them into structured, citation-ready records — with a local-first dashboard and analysis engine on top.

## Architecture

```
PDF
 │
 ▼
Extraction Pipeline (extract/ → verify/ → scopus/)   -- unmodified since Milestone 1 kickoff
 │
 ▼
ImportService (background thread + job polling)
 │
 ▼
Repository layer (repository/) ──► Warehouse DB (biblioflow.sqlite, normalized schema)
 │                                  legacy database.sqlite stays separate (checksum cache only)
 ▼
Analysis Engine (engine/) ──► JSON metrics
 │
 ▼
Dash pages (pages/) -- render only, no SQL in callbacks
```

- **Extraction pipeline** (`src/extract/`, `src/verify/`, `src/scopus/`, `src/export/`) — unchanged since the original CLI pipeline; see "Pipeline" below.
- **`database/`** — normalized SQLite schema (papers, authors, journals, institutions, countries, publishers, keywords, references, projects, events, jobs, analysis_runs, exports) in a separate `biblioflow.sqlite`, independent from the legacy `database.sqlite`.
- **`repository/`** — one repository per entity; pages never touch SQL directly.
- **`services/`** — `ImportService` (background-thread job runner + polling, not a real queue — see Notes), `ProjectService`, `EventService`, `PaperExportService`.
- **`providers/`** — `CrossrefProvider`/`ScopusProvider` wrap the existing fetch functions behind a common `MetadataProvider` interface; `OpenAlexProvider`/`OrcidProvider`/`RorProvider` are explicit stubs for a future milestone.
- **`engine/`** — descriptive bibliometric calculations (dataset overview + metadata completeness, publications, citations, authors, journals, institutions; countries/keywords/references return honest empty results with a `note` explaining the missing data path).

## What's implemented

### Pipeline (`src/extract/`, `verify/`, `scopus/`, `export/`)

1. **Extract** — pulls the paper's own DOI and title from each PDF. DOI detection prioritizes embedded PDF metadata, then a DOI repeated across multiple pages (header/footer), then position on page 1 before any references section — avoiding false positives from citation DOIs in the bibliography.
2. **Verify** — confirms the extracted DOI against CrossRef and fuzzy-matches titles, flagging low-confidence matches for manual review.
3. **Scopus** — fetches metadata (title, journal, citation count, affiliations) from the Scopus Search API by DOI, with local caching. (Full abstracts/keywords/references require Scopus Abstract Retrieval, which needs institutional IP/insttoken access beyond a bare API key — not wired up yet.)
4. **Export** — writes `results.json`, `results.csv`, `results.bib`, and a Scopus-format CSV importable into R's `bibliometrix::convert2df()`.
5. **State tracking** (`src/db.py`) — SQLite-backed checksum cache, so re-runs skip unchanged PDFs unless forced. Untouched by the dashboard/warehouse layer.

### Dashboard (`src/app.py`)

A Dash app reading from the normalized warehouse DB via the repository/engine layers — no mock data anywhere.

- **Dashboard** (`/`) — KPI row (papers, distinct authors, journals, citations, avg citations/paper, avg authors/paper, projects), Metadata Quality card (overall + per-field completeness %), Publication Trend / Top Journals / Citation Distribution charts, Recent Imports, Recent Activity (real event log), Quick Actions.
- **Library** (`/library`) — `dash-ag-grid` table (sort/filter/pagination) over real papers, CSV/Excel export, row click → Paper Details.
- **Paper Details** (`/paper/<id>`) — full metadata, authors, institutions, pipeline status/error, JSON export. Honestly states when abstract/keywords/references aren't available rather than faking them.
- **Import** (`/import`) — shows the PDF folder, runs the pipeline as a background job with live progress polling (button no longer blocks the UI thread).
- **Projects** (`/projects`) — real CRUD (create/rename/delete) backed by `ProjectRepository`, paper counts, creation dates, recent activity feed.
- **Analysis** (`/analysis`) — Overview, Publication Analysis (annual/monthly, CAGR, moving average, forecast), and Citation Analysis (distribution, percentiles, top-cited) tabs are real, computed by `engine/`. Author/Journal/Institution/Country/Keyword/Reference/Funding tabs are marked "Soon" — that's the next milestone slice.
- **Settings** (`/settings`) — masked Scopus key status, CrossRef contact, configured paths.
- **Networks, AI, Reports & Export** — stub pages, explicitly marked "Soon" rather than faking functionality that doesn't exist yet.

Dark theme matches the agreed palette (`#0B1220` background, `#2563EB` primary, etc.) in `src/assets/style.css`.

### Not yet wired

- Universal search bar and notification bell are static placeholders (no command-palette behavior or real notification feed).
- Author/Journal/Institution/Country/Keyword/Reference/Funding analysis, network analysis, AI chat/summarization, and report generation (HTML/PDF/Word/PPT) are all unbuilt — sidebar/tabs show them as "Soon" rather than linking to dead pages.
- Country, keyword, and reference data have no extraction path yet (Scopus Search API doesn't return them; would need Abstract Retrieval or an affiliation→country lookup) — `engine/countries.py`, `engine/keywords.py`, `engine/references.py` return real empty results with a `note` field rather than fabricated numbers.
- Background jobs run on a single Python thread per import, not a real queue/worker — sufficient for single-user local use; `ImportService.start_import()`/`get_job()` is the interface that would stay stable if a real queue is introduced later.

## Setup

```bash
pip install -r requirements.txt
```

Put your Elsevier/Scopus API key (bare string, no `KEY=value`) in `scopus_api.env` at the repo root. This file is gitignored and must never be committed.

## Usage

Launch the dashboard (recommended — runs the pipeline as a background job from the Import page):

```bash
cd src
python3 app.py
```

Then open `http://127.0.0.1:8050`.

Or run the pipeline standalone from the CLI:

```bash
python src/pipeline.py --input PDF/ --output out/
```

If you already have data in the legacy `database.sqlite` and want it reflected in the dashboard, run the one-off migration:

```bash
cd src
python3 migrate_legacy.py
```

Pipeline state is tracked in `src/database.sqlite` so re-runs skip unchanged PDFs unless `--force` is passed. Use `--no-scopus` to skip the Scopus stage.

## Author

Robin Tomar ([itsrobintomar@gmail.com](mailto:itsrobintomar@gmail.com))
