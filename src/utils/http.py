"""HTTP fetch helper used by all scrapers."""

import logging
import time

import httpx

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; DataForGeeks/2.0; "
        "+https://github.com/altrhombus/DataForGeeks)"
    )
}
_TIMEOUT = 30
_MAX_ATTEMPTS = 3
_RETRYABLE_STATUSES = {429, 500, 502, 503, 504}


def get_html(url: str) -> str:
    """Fetch a URL and return the response body as a string.

    Retries up to 3 times with exponential backoff on transient errors
    (429, 5xx, network failures). Non-retryable 4xx errors propagate immediately.
    """
    logger.debug("Fetching %s", url)
    last_exc: Exception | None = None
    with httpx.Client(headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True) as client:
        for attempt in range(_MAX_ATTEMPTS):
            try:
                response = client.get(url)
                if response.status_code in _RETRYABLE_STATUSES:
                    raise httpx.HTTPStatusError(
                        f"HTTP {response.status_code}",
                        request=response.request,
                        response=response,
                    )
                response.raise_for_status()
                return response.text
            except (httpx.TransportError, httpx.HTTPStatusError) as exc:
                last_exc = exc
                if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code not in _RETRYABLE_STATUSES:
                    raise
                if attempt < _MAX_ATTEMPTS - 1:
                    delay = 2**attempt
                    logger.warning("Attempt %d failed for %s (%s) — retrying in %ds", attempt + 1, url, exc, delay)
                    time.sleep(delay)
    raise last_exc  # type: ignore[misc]
