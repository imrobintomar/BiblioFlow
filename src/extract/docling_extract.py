from pathlib import Path
from typing import Optional

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc import DocItemLabel

_PIPELINE_OPTIONS = PdfPipelineOptions(do_ocr=False)
_CONVERTER = DocumentConverter(
    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=_PIPELINE_OPTIONS)}
)

FUNDING_HEADING_KEYWORDS = ("funding", "acknowledg")
ETHICS_HEADING_KEYWORDS = ("ethic", "consent", "irb", "institutional review")
REFERENCES_HEADING_KEYWORDS = ("references", "bibliography")
ABSTRACT_HEADING_KEYWORDS = ("abstract",)


class DoclingDocument:
    """Wraps a converted Docling document with section/caption/table/figure
    access used by the rest of the extraction pipeline."""

    def __init__(self, sections: dict[str, str], captions: list[str], table_count: int, figure_count: int):
        self.sections = sections
        self.captions = captions
        self.table_count = table_count
        self.figure_count = figure_count

    def section_matching(self, keywords: tuple[str, ...]) -> Optional[str]:
        for heading, text in self.sections.items():
            if any(kw in heading.lower() for kw in keywords):
                return text
        return None

    @property
    def abstract(self) -> Optional[str]:
        explicit = self.section_matching(ABSTRACT_HEADING_KEYWORDS)
        if explicit:
            return explicit.strip()

        # Many publishers (e.g. Nature) don't print an explicit "Abstract"
        # heading -- the abstract is just body text before the first real
        # section header. Docling also tags the paper's own title as a
        # SECTION_HEADER, so the abstract paragraph can end up bucketed
        # under the title's key rather than "_preamble". Combine both and
        # keep only prose-length fragments to drop short metadata lines
        # ("Received: ...", "Check for updates", etc.).
        heading_keys = list(self.sections.keys())
        candidate_text = self.sections.get("_preamble", "")
        if len(heading_keys) > 1:
            candidate_text += " " + self.sections[heading_keys[1]]

        sentences = [s.strip() for s in candidate_text.split(".")]
        prose = [s for s in sentences if len(s.split()) >= 8]
        # Real abstracts run ~150-300 words / 5-12 sentences -- cap so we
        # don't swallow unrelated body text that landed in the same bucket.
        prose = prose[:10]
        return (". ".join(prose) + ".").strip() if prose else None

    @property
    def funding_text(self) -> Optional[str]:
        return self.section_matching(FUNDING_HEADING_KEYWORDS)

    @property
    def ethics_text(self) -> Optional[str]:
        return self.section_matching(ETHICS_HEADING_KEYWORDS)

    @property
    def references_text(self) -> Optional[str]:
        return self.section_matching(REFERENCES_HEADING_KEYWORDS)


def convert(pdf_path: Path) -> DoclingDocument:
    result = _CONVERTER.convert(str(pdf_path))
    doc = result.document

    sections: dict[str, str] = {}
    current_heading = "_preamble"
    sections[current_heading] = ""

    for item in doc.texts:
        if item.label == DocItemLabel.SECTION_HEADER:
            current_heading = item.text.strip()
            sections.setdefault(current_heading, "")
        elif item.label in (DocItemLabel.TEXT, DocItemLabel.FOOTNOTE):
            sections[current_heading] = sections.get(current_heading, "") + " " + item.text

    captions = [item.text for item in doc.texts if item.label == DocItemLabel.CAPTION]

    return DoclingDocument(
        sections=sections,
        captions=captions,
        table_count=len(doc.tables),
        figure_count=len(doc.pictures),
    )
