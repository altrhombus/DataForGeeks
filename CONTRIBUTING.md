# Contributing to DataForGeeks

Thank you for your interest in contributing. This document covers the setup process, how to add a new scraper, and PR expectations.

---

## Local Setup

This project uses [uv](https://docs.astral.sh/uv/) for package management.

```bash
git clone https://github.com/altrhombus/DataForGeeks.git
cd DataForGeeks
uv sync
```

To run the full test suite:

```bash
uv run pytest
```

To run a single scraper locally:

```bash
uv run python run.py edge-releases
```

Run `uv run python run.py` with no arguments to see all available scraper names.

---

## Adding a New Scraper

Each dataset requires four things:

1. **A Pydantic model** in `src/models/<vendor>/`
   - Inherit from `BaseModel`
   - Add `model_config = ConfigDict(frozen=True)`
   - Use snake_case field names and inline comments documenting each field

2. **A scraper class** in `src/scrapers/<vendor>/`
   - Inherit from `BaseScraper`
   - Set `dataset`, `dataset_name`, and `sources`
   - Implement `parse(pages: dict[str, str]) -> list[dict]`
   - Raise `ValueError("No X entries parsed — page structure may have changed")` if nothing was parsed

3. **A registry entry** in `src/scrapers/__init__.py`
   - Add `"your-scraper-name": YourScraperClass` to the `REGISTRY` dict

4. **A test fixture and test class**
   - Save representative HTML (or JSON) to `tests/fixtures/<vendor>/`
   - Add a test class to the appropriate `tests/test_*.py` file
   - Test record count, field presence, deduplication, and the ValueError guard

5. **A GitHub Actions workflow** in `.github/workflows/`
   - Copy an existing workflow file and update the scraper name and schedule
   - Output goes to `content/<dataset-path>.json`

---

## Write-If-Changed Philosophy

Scrapers should be idempotent. The `write_if_changed()` utility in `src/utils/json_output.py` only writes a new file if the `data` array changed — timestamps in `metadata` are ignored for comparison purposes. This prevents noisy PRs when nothing meaningful has changed.

---

## PR Expectations

- All tests must pass: `uv run pytest`
- New scrapers must include test fixtures and at least one test class
- Field names must use `snake_case` throughout (model, JSON output, README documentation)
- Add the new dataset to the Dataset Catalog in `README.md`
- Prefer small, focused PRs — one scraper per PR is ideal

---

## Reporting Bugs

If a scraper starts producing wrong output or stops working, please [open an issue](https://github.com/altrhombus/DataForGeeks/issues) using the **Bug Report** template. Include the scraper name and a link to the source page if the page structure has changed.
