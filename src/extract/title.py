from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF

MIN_TITLE_LENGTH = 8
MAX_TITLE_LENGTH = 400


def _spans_by_font_size(page: "fitz.Page") -> list[tuple[float, str, float]]:
    """Returns (font_size, text, y_position) for each text line on the page."""
    spans = []
    page_dict = page.get_text("dict")
    for block in page_dict.get("blocks", []):
        for line in block.get("lines", []):
            line_text = "".join(span["text"] for span in line.get("spans", [])).strip()
            if not line_text:
                continue
            max_size = max(span["size"] for span in line.get("spans", []))
            y_pos = line["bbox"][1]
            spans.append((max_size, line_text, y_pos))
    return spans


def extract_title(pdf_path: Path) -> Optional[str]:
    """Heuristic: the title is the largest-font text block in the top half
    of page 1 (falls back to page 2 if page 1 yields nothing usable)."""
    doc = fitz.open(pdf_path)
    try:
        for page_idx in (0, 1):
            if page_idx >= len(doc):
                continue
            page = doc[page_idx]
            page_height = page.rect.height
            spans = _spans_by_font_size(page)
            top_half = [s for s in spans if s[2] < page_height * 0.6]
            candidates = top_half or spans
            if not candidates:
                continue

            max_size = max(c[0] for c in candidates)
            title_lines = [
                c[1] for c in candidates if c[0] >= max_size - 0.5
            ]
            title = " ".join(title_lines).strip()

            if MIN_TITLE_LENGTH <= len(title) <= MAX_TITLE_LENGTH:
                return title
        return None
    finally:
        doc.close()
