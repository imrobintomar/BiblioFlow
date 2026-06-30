# BiblioFlow

A bibliometric analysis platform that takes downloaded PDFs and turns them into structured, citation-ready records — with a local-first, biblioshiny-style dashboard and analysis engine on top.

## Architecture

```
PDF
 │
 ▼
Extraction Pipeline (extract/ → verify/ → scopus/)        -- unmodified since Milestone 1 kickoff
 │  + Docling structural extraction (sections, abstract, funding/ethics text, tables/figures)
 │  + regex extraction (keywords, trial IDs, ORCID, grant IDs, known funders)
 ▼
ImportService (background thread + job polling)
 │
 ▼
Free metadata-enrichment waterfall (providers/)
   CrossRef → OpenAlex → Semantic Scholar → PubMed (conditional) → Unpaywall → ROR (backfill)
 │  each provider only fills fields the previous ones left empty
 ▼
Repository layer (repository/) ──► Warehouse DB (biblioflow.sqlite, normalized schema)
 │                                  legacy database.sqlite stays separate (checksum cache only)
 │                                  + field_provenance: source/method/confidence per field per paper
 ▼
Analysis Engine (engine/) ──► JSON metrics (descriptive bibliometrics + network science)
 │
 ▼
Dash pages (pages/) -- biblioshiny-style sections, render only, no SQL in callbacks
```

- **Extraction pipeline** (`src/extract/`, `src/verify/`, `src/scopus/`, `src/export/`) — DOI/title extraction logic unchanged since the original CLI pipeline. Extended (additively) with Docling-based structural extraction and regex-based text patterns — see "Pipeline" below.
- **`database/`** — normalized SQLite schema (papers, authors, journals, institutions, countries, publishers, keywords, funders, reference_entries, projects, events, jobs, field_provenance, analysis_runs, exports) in a separate `biblioflow.sqlite`, independent from the legacy `database.sqlite`.
- **`repository/`** — one repository per entity; pages never touch SQL directly. `update_fields_if_empty()` implements the enrichment waterfall semantics (never clobber a higher-priority source's value).
- **`services/`** — `ImportService` (background-thread job runner + polling, not a real queue — see Notes), `EnrichmentService` (runs the provider waterfall per paper), `ProjectService`, `EventService`, `PaperExportService`.
- **`providers/`** — `CrossrefProvider`, `ScopusProvider`, `OpenAlexProvider`, `SemanticScholarProvider`, `PubMedProvider`, `UnpaywallProvider`, `RorProvider`, `OrcidProvider` — all real, live-verified implementations behind a common `MetadataProvider` interface.
- **`engine/`** — descriptive bibliometrics (dataset overview, publications, citations, authors, journals, institutions, publishers, countries, keywords, references, funding, documents, languages) plus network science (`network_utils`, `clustering`, `thematic`, `intellectual_structure`, `social_networks` — built on NetworkX). Fields with no real data path return honest empty results with a `note` explaining why, never fabricated numbers.
- **`pages/analysis_shared.py`** — shared chart helpers and the "Top N items" control bar used across every section page.

## What's implemented

### Pipeline (`src/extract/`, `verify/`, `scopus/`, `export/`)

1. **Extract** — pulls the paper's own DOI and title from each PDF (metadata → multi-page frequency → position-before-references fallback, avoiding citation-list false positives). **Docling** (layout-aware PDF parsing, OCR disabled since sources are digital-native) extracts sections, abstract, table/figure counts, and funding/ethics/references text blocks. Regex passes extract keywords, trial IDs (NCT-pattern), ORCID IDs, consent statements, and known-funder/grant-ID matches.
2. **Verify** — confirms the extracted DOI against CrossRef, fuzzy-matches titles, and captures previously-unused CrossRef fields (publisher, page range, document type, language).
3. **Scopus** — fetches metadata from the Scopus Search API by DOI (Abstract Retrieval needs institutional access this key doesn't have, so Search API is the ceiling here).
4. **Enrichment waterfall** (`services/enrichment_service.py`) — after the pipeline above, runs OpenAlex (country, institutions+ROR, concepts, full references, grants, abstract/OA backfill) → Semantic Scholar (abstract/references backfill, fields of study, rate-limited to the approved key's 1 req/s grant) → PubMed (conditional on a resolved PMID; MeSH terms, grant IDs) → Unpaywall (OA status/URL backfill) → ROR (institution→country backfill, with cross-source country-name normalization via `pycountry`). Every filled field is logged in `field_provenance` (source, method, confidence).
5. **Export** — writes `results.json`, `results.csv`, `results.bib`, and a Scopus-format CSV importable into R's `bibliometrix::convert2df()`.
6. **State tracking** (`src/db.py`) — SQLite-backed checksum cache, so re-runs skip unchanged PDFs unless forced. Untouched by the dashboard/warehouse layer.

### Dashboard (`src/app.py`)

A Dash app, restructured to follow **biblioshiny's actual navigation and interaction conventions** (in BiblioFlow's own Navy/Teal-Blue brand palette — `#040924` / `#052659` / `#5483B3` / `#7DA0CA` / `#C1E8FF`), reading entirely from the normalized warehouse DB via the repository/engine layers — no mock data anywhere.

Every analysis result follows the same **biblioshiny-style panel** (`components.biblio_panel`): a "Main Information" summary block, then chart + its underlying data table side-by-side, with a CSV download and a PNG download built into the chart's mode bar. Most sections also have a live **"Top N items" slider** (one control drives every rank-ordered panel on that page, matching biblioshiny's actual UX, not a separate control per chart).

- **Dashboard** (`/`) — full Module-1 KPI set (corpus size, averages & collaboration, growth & data quality, data-source distribution, metadata completeness/confidence, duplication rate), Publication Trend / Top Journals / Citation Distribution panels, Recent Imports, Recent Activity, Project Summary, Quick Actions.
- **Library** (`/library`) — `dash-ag-grid` table over real papers, CSV/Excel export, row click → Paper Details.
- **Paper Details** (`/paper/<id>`) — full metadata, authors, institutions, pipeline status/error, JSON export.
- **Import** (`/import`) — background-job pipeline run with live progress polling.
- **Projects** (`/projects`) — real CRUD, paper counts, recent activity feed.
- **Overview** (`/overview`) — dataset overview + full Publication Analysis (annual/monthly/quarterly/decade, CAGR, moving average, forecast, cumulative, density, heatmap/calendar, growth by document type/country/institution/journal).
- **Sources** (`/sources`) — Journals (Bradford's Law/zones, citation impact, H-index, timeline, OA), Publishers, Document Types (incl. OA/license distribution), Languages.
- **Authors** (`/authors`) — Productivity (full + fractional counting), Citation Metrics (H/G/M/i10/contemporary-H/normalized-H, citation velocity, local-vs-global citations), Collaboration, Career; plus an **Institutions (Affiliations)** tab (most productive, growth, citation impact, collaboration edges, top researchers, timeline, country/funding distribution).
- **Documents** (`/documents`) — Citations (distribution, percentiles, top-cited), References (most cited within corpus), Funding.
- **Clustering** (`/clustering`) — co-authorship, keyword co-occurrence, bibliographic coupling, and local citation networks, each with full centrality (degree/betweenness/closeness/eigenvector/PageRank), network metrics (density, diameter, components, clustering coefficient, assortativity), and Louvain community detection.
- **Conceptual Structure** (`/conceptual-structure`) — Keywords, plus a Thematic Map / Strategic Diagram (Callon centrality/density quadrants from keyword-cluster co-occurrence) and Theme Evolution across year-halves.
- **Intellectual Structure** (`/networks`) — Reference co-citation (top co-cited pairs), Historiograph/citation tree.
- **Social Structure** (`/social-structure`) — Countries, Author/Institution/Country collaboration networks, Collaboration Timeline.
- **Settings** (`/settings`) — masked API key status, CrossRef contact, configured paths.
- **AI, Reports & Export** — stub pages, explicitly marked "Soon."

### Not yet wired / known limitations (flagged honestly in the UI, not hidden)

- Universal search bar and notification bell are static placeholders.
- AI chat/summarization and full report generation (HTML/PDF/Word/PPT) are unbuilt — marked "Soon."
- **Author/institution attribution is paper-level, not true per-author**: the schema links papers to institutions, not individual authors to their specific institution, so a co-author's affiliation can't be isolated from the author's own (affects Author Collaboration, Top Researchers per Institution, Funding Distribution).
- **Author/Journal Co-citation networks aren't implemented** — they'd require resolving every individual reference's own authors/journal via an extra API call per reference (400+ reference links in even this small corpus).
- **Citation Half-Life isn't computable** — every source gives a single cumulative citation count, not a citation-by-year timeline.
- **Bibliographic coupling/reference co-citation accuracy is bounded by DOI resolution** — only Semantic Scholar references currently resolve to a DOI; OpenAlex's `referenced_works` aren't DOI-resolved, so cross-paper reference matching undercounts until that's added.
- **True MCA/Correspondence Analysis isn't implemented** — the Thematic Map uses real co-word clustering (Louvain on a keyword co-occurrence network) as a simpler substitute, not the more rigorous dimensionality-reduction technique bibliometrix also offers.
- Institution/country names aren't deduplicated across sources (e.g. minor spelling/quote-mark variants from different providers can appear as separate entities).
- Background jobs run on a single Python thread per import, not a real queue/worker — sufficient for single-user local use; `ImportService.start_import()`/`get_job()` is the interface that would stay stable if a real queue is introduced later.

## Setup

This project uses **Docling** for PDF structural extraction, which pulls in heavy ML dependencies (`transformers`, `accelerate`) that can conflict with packages in a shared conda/anaconda base environment. Use a dedicated virtualenv:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Put your Elsevier/Scopus API key (bare string, no `KEY=value`) in `scopus_api.env`, and your Semantic Scholar API key in `semantic_scholar_api.env`, both at the repo root. Both files are gitignored and must never be committed.

## Usage

Launch the dashboard (recommended — runs the pipeline as a background job from the Import page):

```bash
cd src
../.venv/bin/python3 app.py
```

Then open `http://127.0.0.1:8050`.

Or run the pipeline standalone from the CLI:

```bash
../.venv/bin/python3 src/pipeline.py --input PDF/ --output out/
```

If you already have data in the legacy `database.sqlite` and want it reflected in the dashboard, run the one-off migration:

```bash
cd src
../.venv/bin/python3 migrate_legacy.py
```

Pipeline state is tracked in `src/database.sqlite` so re-runs skip unchanged PDFs unless `--force` is passed. Use `--no-scopus` to skip the Scopus stage. The warehouse DB (`src/biblioflow.sqlite`) is fully derived/rebuildable from the legacy state — safe to delete and re-migrate.

## Design

See [`VISUALIZATION_GUIDELINES.md`](VISUALIZATION_GUIDELINES.md) for the chart-type-per-analysis reference (e.g. Treemap for Journals/Publishers, Bubble for Authors/Institutions, Choropleth for Countries) and the grid-layout principle — several existing pages still default to horizontal bar charts and are a known retrofit target against that guide, not yet executed.

## Author

Robin Tomar ([itsrobintomar@gmail.com](mailto:itsrobintomar@gmail.com))
