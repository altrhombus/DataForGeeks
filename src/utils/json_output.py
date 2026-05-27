import json
from datetime import UTC, datetime
from pathlib import Path

from src.scrapers.base import BaseScraper


def build_envelope(scraper: BaseScraper, data: list[dict]) -> dict:
    return {
        "schema_version": "2.0",
        "dataset": scraper.dataset,
        "last_updated_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sources": scraper.sources,
        "record_count": len(data),
        "data": data,
    }


def write_if_changed(output_path: Path, envelope: dict) -> bool:
    """Write envelope to disk only if the data changed. Returns True if written."""
    if output_path.exists():
        existing = json.loads(output_path.read_text(encoding="utf-8"))
        if existing.get("data") == envelope.get("data"):
            print("No changes detected.")
            return False
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(envelope, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Updated: {output_path}")
    return True
