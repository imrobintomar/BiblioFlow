import re

KEYWORDS_REGEX = re.compile(r"(?:key\s*words?)\s*[:\-]\s*(.+)", re.IGNORECASE)
TRIAL_ID_REGEX = re.compile(r"\bNCT\d{8}\b", re.IGNORECASE)
ORCID_REGEX = re.compile(r"\b\d{4}-\d{4}-\d{4}-\d{3}[\dX]\b")
CONSENT_REGEX = re.compile(r"[^.]*\binformed consent\b[^.]*\.", re.IGNORECASE)
GRANT_ID_REGEX = re.compile(
    r"\b(?:[A-Z]{1,5}\d{2,3}[A-Z]{2}\d{5,8}|Grant\s*(?:No\.?|#)?\s*[:\-]?\s*[A-Z0-9\-/]{4,20})\b",
    re.IGNORECASE,
)

KNOWN_FUNDERS = [
    "National Institutes of Health",
    "NIH",
    "National Science Foundation",
    "NSF",
    "Wellcome Trust",
    "European Commission",
    "Horizon 2020",
    "European Research Council",
    "Medical Research Council",
    "Bill and Melinda Gates Foundation",
    "Gates Foundation",
    "Deutsche Forschungsgemeinschaft",
    "DFG",
    "World Health Organization",
    "WHO",
    "Chinese Academy of Sciences",
    "National Natural Science Foundation of China",
    "UK Research and Innovation",
    "UKRI",
    "Howard Hughes Medical Institute",
]


def extract_keywords(full_text: str) -> list[str]:
    match = KEYWORDS_REGEX.search(full_text)
    if not match:
        return []
    raw = match.group(1)
    # Keywords lines usually end at the next sentence/section; cut at first
    # period followed by a capital letter to avoid swallowing body text.
    raw = re.split(r"\.\s+[A-Z]", raw)[0]
    parts = re.split(r"[;,]", raw)
    return [p.strip().rstrip(".") for p in parts if p.strip() and len(p.strip()) < 60]


def extract_trial_ids(full_text: str) -> list[str]:
    return sorted(set(m.upper() for m in TRIAL_ID_REGEX.findall(full_text)))


def extract_orcids(full_text: str) -> list[str]:
    return sorted(set(ORCID_REGEX.findall(full_text)))


def extract_consent_statement(full_text: str) -> str | None:
    match = CONSENT_REGEX.search(full_text)
    return match.group(0).strip() if match else None


def extract_grant_ids(funding_text: str) -> list[str]:
    if not funding_text:
        return []
    return sorted(set(GRANT_ID_REGEX.findall(funding_text)))


def extract_known_funders(text: str) -> list[str]:
    if not text:
        return []
    found = []
    for funder in KNOWN_FUNDERS:
        if re.search(rf"\b{re.escape(funder)}\b", text, re.IGNORECASE):
            found.append(funder)
    return found
