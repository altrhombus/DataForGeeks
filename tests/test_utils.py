"""Tests for src/utils/http.py, json_output.py, and scraper_helpers.py."""

import json
from unittest.mock import MagicMock, call, patch

import httpx
import pytest

from src.exceptions import RecordCountDropError
from src.scrapers.base import BaseScraper
from src.utils.http import _HEADERS, get_html
from src.utils.json_output import build_envelope, write_if_changed
from src.utils.scraper_helpers import (
    deduplicate_sorted,
    kb_article_url,
    normalize_ms_url,
    parse_date,
)

# ---------------------------------------------------------------------------
# http.py
# ---------------------------------------------------------------------------


def _make_client_patch(mock_client):
    """Return a patch target that wires __enter__/__exit__ to mock_client."""
    cls = MagicMock()
    cls.return_value.__enter__ = MagicMock(return_value=mock_client)
    cls.return_value.__exit__ = MagicMock(return_value=False)
    return cls


def _mock_response(status_code: int, text: str = "<html>ok</html>") -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    resp.request = MagicMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            str(status_code), request=resp.request, response=resp
        )
    return resp


def test_get_html_success():
    mock_client = MagicMock()
    mock_client.get.return_value = _mock_response(200)

    with patch("src.utils.http.httpx.Client", _make_client_patch(mock_client)):
        result = get_html("https://example.com")

    assert result == "<html>ok</html>"
    assert mock_client.get.call_count == 1


def test_get_html_user_agent_header():
    assert "DataForGeeks" in _HEADERS["User-Agent"]


def test_get_html_raises_immediately_on_404():
    """404 is not retryable — should raise after exactly one attempt."""
    mock_client = MagicMock()
    mock_client.get.return_value = _mock_response(404)

    with (
        patch("src.utils.http.httpx.Client", _make_client_patch(mock_client)),
        patch("src.utils.http.time.sleep") as mock_sleep,
        pytest.raises(httpx.HTTPStatusError),
    ):
        get_html("https://example.com/missing")

    assert mock_client.get.call_count == 1
    mock_sleep.assert_not_called()


def test_get_html_retries_on_429_then_raises():
    """429 is retryable — all 3 attempts fail, final exception is raised."""
    mock_client = MagicMock()
    mock_client.get.return_value = _mock_response(429)

    with (
        patch("src.utils.http.httpx.Client", _make_client_patch(mock_client)),
        patch("src.utils.http.time.sleep") as mock_sleep,
        pytest.raises(httpx.HTTPStatusError),
    ):
        get_html("https://example.com/throttled")

    assert mock_client.get.call_count == 3
    assert mock_sleep.call_args_list == [call(1), call(2)]


def test_get_html_retries_on_transport_error_then_raises():
    """Network errors are retried up to 3 times."""
    mock_client = MagicMock()
    mock_client.get.side_effect = httpx.TransportError("connection reset")

    with (
        patch("src.utils.http.httpx.Client", _make_client_patch(mock_client)),
        patch("src.utils.http.time.sleep") as mock_sleep,
        pytest.raises(httpx.TransportError),
    ):
        get_html("https://example.com/flaky")

    assert mock_client.get.call_count == 3
    assert mock_sleep.call_args_list == [call(1), call(2)]


def test_get_html_succeeds_after_transient_failure():
    """Succeeds on the second attempt when first returns a transient 503."""
    mock_client = MagicMock()
    mock_client.get.side_effect = [
        _mock_response(503),
        _mock_response(200),
    ]

    with (
        patch("src.utils.http.httpx.Client", _make_client_patch(mock_client)),
        patch("src.utils.http.time.sleep"),
    ):
        result = get_html("https://example.com/flaky")

    assert result == "<html>ok</html>"
    assert mock_client.get.call_count == 2


# ---------------------------------------------------------------------------
# json_output.py
# ---------------------------------------------------------------------------


class _FakeScraper(BaseScraper):
    dataset = "test/dataset"
    dataset_name = "test-dataset"
    sources = ["https://example.com"]

    def parse(self, pages: dict[str, str]) -> list[dict]:
        return []


def test_write_if_changed_creates_new_file(tmp_path):
    out = tmp_path / "sub" / "out.json"
    scraper = _FakeScraper()
    data = [{"key": "value"}]
    envelope = build_envelope(scraper, data)

    result = write_if_changed(out, envelope)

    assert result is True
    assert out.exists()
    written = json.loads(out.read_text())
    assert written["data"] == data


def test_write_if_changed_creates_parent_dirs(tmp_path):
    out = tmp_path / "a" / "b" / "c" / "out.json"
    envelope = build_envelope(_FakeScraper(), [{"x": 1}])

    write_if_changed(out, envelope)

    assert out.exists()


def test_write_if_changed_skips_when_data_unchanged(tmp_path):
    out = tmp_path / "out.json"
    scraper = _FakeScraper()
    data = [{"key": "value"}]
    envelope = build_envelope(scraper, data)

    write_if_changed(out, envelope)
    mtime_before = out.stat().st_mtime

    # Write again with same data but different metadata timestamp
    envelope2 = build_envelope(scraper, data)
    result = write_if_changed(out, envelope2)

    assert result is False
    assert out.stat().st_mtime == mtime_before


def test_write_if_changed_overwrites_when_data_changed(tmp_path):
    out = tmp_path / "out.json"
    scraper = _FakeScraper()

    write_if_changed(out, build_envelope(scraper, [{"v": 1}]))
    result = write_if_changed(out, build_envelope(scraper, [{"v": 2}]))

    assert result is True
    written = json.loads(out.read_text())
    assert written["data"] == [{"v": 2}]


def test_write_if_changed_rejects_large_count_drop(tmp_path):
    out = tmp_path / "out.json"
    scraper = _FakeScraper()

    write_if_changed(out, build_envelope(scraper, [{"v": i} for i in range(100)]))

    with pytest.raises(RecordCountDropError, match="dropped from 100 to 10"):
        write_if_changed(out, build_envelope(scraper, [{"v": i} for i in range(10)]))
    # original file untouched
    assert json.loads(out.read_text())["metadata"]["recordCount"] == 100


def test_write_if_changed_allows_small_count_drop(tmp_path):
    out = tmp_path / "out.json"
    scraper = _FakeScraper()

    write_if_changed(out, build_envelope(scraper, [{"v": i} for i in range(100)]))
    result = write_if_changed(out, build_envelope(scraper, [{"v": i} for i in range(95)]))

    assert result is True


def test_write_if_changed_allows_count_growth(tmp_path):
    out = tmp_path / "out.json"
    scraper = _FakeScraper()

    write_if_changed(out, build_envelope(scraper, [{"v": 1}]))
    result = write_if_changed(out, build_envelope(scraper, [{"v": i} for i in range(50)]))

    assert result is True


def test_write_if_changed_count_drop_override(tmp_path, monkeypatch):
    out = tmp_path / "out.json"
    scraper = _FakeScraper()
    monkeypatch.setenv("ALLOW_RECORD_COUNT_DROP", "1")

    write_if_changed(out, build_envelope(scraper, [{"v": i} for i in range(100)]))
    result = write_if_changed(out, build_envelope(scraper, [{"v": 1}]))

    assert result is True
    assert json.loads(out.read_text())["metadata"]["recordCount"] == 1


def test_build_envelope_structure():
    scraper = _FakeScraper()
    data = [{"a": 1}]
    env = build_envelope(scraper, data)

    assert env["metadata"]["provider"] == "DataForGeeks"
    assert env["metadata"]["apiVersion"] == "v2"
    assert env["metadata"]["dataset"] == "test-dataset"
    assert env["metadata"]["recordCount"] == 1
    assert env["metadata"]["sourceUrls"] == ["https://example.com"]
    assert env["data"] == data


# ---------------------------------------------------------------------------
# scraper_helpers.py
# ---------------------------------------------------------------------------


def test_deduplicate_sorted_basic():
    records = [3, 1, 2, 1, 3]
    result = deduplicate_sorted(records, sort_key=lambda r: r)
    assert result == [1, 2, 3]


def test_deduplicate_sorted_reverse():
    records = [3, 1, 2, 1, 3]
    result = deduplicate_sorted(records, sort_key=lambda r: r, reverse=True)
    assert result == [3, 2, 1]


def test_deduplicate_sorted_with_key_fn():
    records = [{"id": 1, "v": "a"}, {"id": 2, "v": "b"}, {"id": 1, "v": "c"}]
    result = deduplicate_sorted(records, sort_key=lambda r: r["id"], key_fn=lambda r: r["id"])
    assert len(result) == 2
    assert result[0]["id"] == 1
    assert result[1]["id"] == 2


def test_deduplicate_sorted_empty():
    assert deduplicate_sorted([], sort_key=lambda r: r) == []


def test_parse_date_month_dd_yyyy():
    assert parse_date("May 13, 2026") == "2026-05-13"


def test_parse_date_dd_mon_yyyy():
    assert parse_date("13 May 2026") == "2026-05-13"


def test_parse_date_strips_whitespace():
    assert parse_date("  May 13, 2026  ") == "2026-05-13"


def test_parse_date_empty_returns_none():
    assert parse_date("") is None
    assert parse_date("   ") is None


def test_parse_date_invalid_returns_none():
    assert parse_date("not a date") is None
    assert parse_date("2026-05-13") is None  # ISO not in default formats


def test_parse_date_custom_formats():
    result = parse_date("2026-05-13", formats=["%Y-%m-%d"])
    assert result == "2026-05-13"


def test_normalize_ms_url_absolute():
    url = "https://support.microsoft.com/en-us/topic/kb12345"
    assert normalize_ms_url(url) == url


def test_normalize_ms_url_relative():
    assert normalize_ms_url("/en-us/topic/kb12345") == "https://support.microsoft.com/en-us/topic/kb12345"


def test_normalize_ms_url_empty_returns_none():
    assert normalize_ms_url("") is None
    assert normalize_ms_url("   ") is None


def test_normalize_ms_url_unrecognised_returns_none():
    assert normalize_ms_url("javascript:void(0)") is None


def test_kb_article_url_standard():
    assert kb_article_url("KB5099539") == "https://support.microsoft.com/help/5099539"


def test_kb_article_url_lowercase_prefix():
    assert kb_article_url("kb5099539") == "https://support.microsoft.com/help/5099539"


def test_kb_article_url_invalid_returns_none():
    assert kb_article_url("KBabc") is None
    assert kb_article_url("") is None
