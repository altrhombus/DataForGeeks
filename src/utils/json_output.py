import json
from datetime import UTC, datetime
from pathlib import Path

from src.scrapers.base import BaseScraper


def build_envelope(scraper: BaseScraper, data: list[dict]) -> dict:
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    label = scraper.dataset_name or scraper.dataset
    return {
        "metadata": {
            "provider": "DataForGeeks",
            "apiVersion": "v2",
            "dataset": label,
            "recordCount": len(data),
            "sourceUrls": scraper.sources,
            "lastModified": now,
            "lastCollected": now,
        },
        "data": data,
    }


def write_if_changed(output_path: Path, envelope: dict) -> bool:
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
