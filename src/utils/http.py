import httpx

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; DataForGeeks/2.0; "
        "+https://github.com/altrhombus/DataForGeeks)"
    )
}
_TIMEOUT = 30


def get_html(url: str) -> str:
    """Fetch a URL and return the response body as a string."""
    with httpx.Client(headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.text
