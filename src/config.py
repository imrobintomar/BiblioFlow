from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = Path(__file__).resolve().parent

PDF_DIR = ROOT_DIR / "PDF"
CACHE_DIR = SRC_DIR / "cache"
LOGS_DIR = SRC_DIR / "logs"
DB_PATH = SRC_DIR / "database.sqlite"
# Separate normalized warehouse DB for the dashboard/analysis layer.
# DB_PATH (pipeline_state) stays untouched -- it's only the extraction
# pipeline's checksum/skip-logic cache.
WAREHOUSE_DB_PATH = SRC_DIR / "biblioflow.sqlite"
EXPORT_DIR = ROOT_DIR / "out"

CACHE_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
EXPORT_DIR.mkdir(exist_ok=True)

_env_path = ROOT_DIR / "scopus_api.env"
# scopus_api.env holds a single bare API key (no KEY=value format).
SCOPUS_API_KEY = _env_path.read_text().strip() if _env_path.exists() else None

_s2_env_path = ROOT_DIR / "semantic_scholar_api.env"
SEMANTIC_SCHOLAR_API_KEY = _s2_env_path.read_text().strip() if _s2_env_path.exists() else None

CROSSREF_MAILTO = "itsrobintomar@gmail.com"
CROSSREF_BASE_URL = "https://api.crossref.org/works"

TITLE_FUZZY_MATCH_THRESHOLD = 80
