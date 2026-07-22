"""Custom exception hierarchy for DataForGeeks scrapers."""


class ScraperError(Exception):
    """Base class for all scraper errors."""


class ParseError(ScraperError):
    """Raised when a scraper cannot parse expected content from a page."""


class StructureChangedError(ParseError):
    """Raised when a page's structure no longer matches what the scraper expects.

    This typically means the source site has been redesigned and the scraper
    needs to be updated.
    """


class RecordCountDropError(ScraperError):
    """Raised when a new dataset would shrink sharply versus the published one.

    A large drop almost always means a partial parse failure (some sources
    silently yielding zero records) rather than genuine upstream removal.
    """
