# BiblioFlow

A bibliometric analysis pipeline that takes downloaded PDFs and turns them into structured, citation-ready records.

## Pipeline

1. **Extract** (`src/extract/`) — pulls the paper's own DOI and title from each PDF. DOI detection prioritizes embedded PDF metadata, then a DOI repeated across multiple pages (header/footer), then position on page 1 before any references section — avoiding false positives from citation DOIs in the bibliography.
2. **Verify** (`src/verify/`) — confirms the extracted DOI against CrossRef and fuzzy-matches titles, flagging low-confidence matches for manual review.
3. **Scopus** (`src/scopus/`) — fetches metadata (title, journal, citation count, affiliations) from the Scopus Search API by DOI, with local caching.
4. **Export** (`src/export/`) — writes `results.json`, `results.csv`, `results.bib`, and a Scopus-format CSV importable into R's `bibliometrix::convert2df()`.

## Setup

```bash
pip install -r requirements.txt
```

Put your Elsevier/Scopus API key (bare string, no `KEY=value`) in `scopus_api.env` at the repo root. This file is gitignored and must never be committed.

## Usage

```bash
python src/pipeline.py --input PDF/ --output out/
```

Pipeline state is tracked in `src/database.sqlite` so re-runs skip unchanged PDFs unless `--force` is passed. Use `--no-scopus` to skip the Scopus stage.

## Notes

- Full author lists, abstracts, keywords, and reference lists require Scopus Abstract Retrieval, which needs institutional (IP or insttoken) access beyond a bare API key.

## Author

Robin Tomar ([itsrobintomar@gmail.com](mailto:itsrobintomar@gmail.com))
