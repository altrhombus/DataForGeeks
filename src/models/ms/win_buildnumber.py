from pydantic import BaseModel


class WinBuildNumber(BaseModel):
    full_version: str   # e.g. "10.0.22621.5192"
    build: str          # e.g. "22621.5192"
    release_date: str   # ISO 8601 date, e.g. "2026-05-13"
    kb_article: str     # e.g. "KB5058411"
    kb_title: str       # full title string
    ltsc_only: bool
    comment: str        # empty string or "Hotpatch"
