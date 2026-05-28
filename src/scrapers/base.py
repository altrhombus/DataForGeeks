"""Abstract base class shared by all DataForGeeks scrapers."""

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Base class for all scrapers. Subclasses define dataset, sources, and parse()."""
    dataset: str        # slug that doubles as output path, e.g. "ms/win/buildnumbers"
    dataset_name: str = ""  # human-readable envelope label; falls back to dataset if empty
    sources: list[str]  # URLs included in the JSON envelope

    def fetch(self) -> dict[str, str]:
        """Fetch all source URLs. Returns {url: html}."""
        from src.utils.http import get_html
        return {url: get_html(url) for url in self.sources}

    @abstractmethod
    def parse(self, pages: dict[str, str]) -> list[dict]:
        """Parse fetched HTML into a list of record dicts."""
        ...

    def run(self) -> list[dict]:
        logger.info("Running %s (%s)", self.__class__.__name__, self.dataset)
        data = self.parse(self.fetch())
        logger.info("Parsed %d records from %s", len(data), self.dataset)
        return data
