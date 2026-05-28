"""Entry point for all scrapers.

Usage:
    python run.py <scraper-name>

Example:
    python run.py win-buildnumbers
"""

import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

CONTENT_DIR = Path(__file__).parent / "content"


def main() -> None:
    from src.exceptions import ScraperError
    from src.scrapers import REGISTRY
    from src.utils.json_output import build_envelope, write_if_changed

    if len(sys.argv) < 2:
        print(f"Usage: python run.py <scraper>\nAvailable: {', '.join(sorted(REGISTRY))}")
        sys.exit(1)

    name = sys.argv[1]
    if name not in REGISTRY:
        print(f"Unknown scraper: {name!r}\nAvailable: {', '.join(sorted(REGISTRY))}")
        sys.exit(1)

    try:
        scraper = REGISTRY[name]()
        data = scraper.run()
    except ScraperError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    if not data:
        print("ERROR: No records parsed — page structure may have changed.", file=sys.stderr)
        sys.exit(1)

    envelope = build_envelope(scraper, data)
    output_path = CONTENT_DIR / (scraper.dataset + ".json")
    write_if_changed(output_path, envelope)


if __name__ == "__main__":
    main()
