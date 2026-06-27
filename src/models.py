from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator

DOI_PATTERN = r"^10\.\d{4,9}/[-._;()/:A-Za-z0-9]+$"


class PipelineStatus(str, Enum):
    PENDING = "pending"
    EXTRACTED = "extracted"
    EXTRACT_FAILED = "extract_failed"
    VERIFIED = "verified"
    VERIFY_FAILED = "verify_failed"
    NEEDS_REVIEW = "needs_review"
    SCOPUS_FETCHED = "scopus_fetched"
    SCOPUS_FAILED = "scopus_failed"
    DONE = "done"


class ExtractedRecord(BaseModel):
    filename: str
    checksum: str
    extracted_title: Optional[str] = None
    extracted_doi: Optional[str] = None
    doi_source: Optional[str] = None  # "metadata" | "frequency" | "position"
    doi_occurrence_pages: int = 0

    @field_validator("extracted_doi")
    @classmethod
    def validate_doi_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip().rstrip(".,;)")
        return v


class CrossrefVerification(BaseModel):
    doi: str
    crossref_title: Optional[str] = None
    crossref_authors: list[str] = Field(default_factory=list)
    journal: Optional[str] = None
    year: Optional[int] = None
    match_score: float = 0.0
    is_confident_match: bool = False


class ScopusRecord(BaseModel):
    doi: str
    eid: Optional[str] = None
    title: Optional[str] = None
    authors: list[str] = Field(default_factory=list)
    affiliations: list[str] = Field(default_factory=list)
    abstract: Optional[str] = None
    keywords: list[str] = Field(default_factory=list)
    cited_by_count: Optional[int] = None
    source_title: Optional[str] = None
    publication_date: Optional[str] = None
    references: list[str] = Field(default_factory=list)
    raw: Optional[dict] = None


class PipelineRecord(BaseModel):
    filename: str
    checksum: str
    status: PipelineStatus = PipelineStatus.PENDING
    extracted: Optional[ExtractedRecord] = None
    crossref: Optional[CrossrefVerification] = None
    scopus: Optional[ScopusRecord] = None
    error: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)
