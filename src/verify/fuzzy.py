from rapidfuzz import fuzz


def title_similarity(extracted_title: str, crossref_title: str) -> float:
    if not extracted_title or not crossref_title:
        return 0.0
    return fuzz.token_sort_ratio(extracted_title.lower(), crossref_title.lower())
