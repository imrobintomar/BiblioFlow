from abc import ABC, abstractmethod
from typing import Optional


class MetadataProvider(ABC):
    """Common interface for any source that can enrich a paper by DOI."""

    name: str

    @abstractmethod
    def fetch_by_doi(self, doi: str) -> Optional[dict]:
        raise NotImplementedError
