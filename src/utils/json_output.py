"""JSON envelope builder and write-if-changed output helper."""

import json
import os
from datetime import UTC, datetime
from pathlib import Path

from src.exceptions import RecordCountDropError
from src.scrapers.base import BaseScraper

# Refuse to publish when the new record count falls below this fraction of the
# previously published count. Guards against partial parse failures that leave
# a non-empty (but gutted) record list — the failure mode that shipped a
# 1,869 → 10 record collapse on 2026-07-14. Set ALLOW_RECORD_COUNT_DROP=1 to
# override for intentional shrinkage (e.g. upstream removed a product line).
_MIN_COUNT_RATIO = 0.9


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
        _check_record_count_drop(existing, envelope, output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(envelope, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Updated: {output_path}")
    return True


def _check_record_count_drop(existing: dict, envelope: dict, output_path: Path) -> None:
    if os.environ.get("ALLOW_RECORD_COUNT_DROP") == "1":
        return
    old_count = len(existing.get("data") or [])
    new_count = len(envelope.get("data") or [])
    if old_count > 0 and new_count < old_count * _MIN_COUNT_RATIO:
        raise RecordCountDropError(
            f"Refusing to write {output_path.name}: record count dropped from "
            f"{old_count} to {new_count} (below {_MIN_COUNT_RATIO:.0%} threshold) — "
            f"likely a partial parse failure. Set ALLOW_RECORD_COUNT_DROP=1 to override."
        )
