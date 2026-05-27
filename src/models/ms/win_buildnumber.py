from pydantic import BaseModel


class WinBuildNumber(BaseModel):
    full_version: str    # "10.0.22621.5039"
    build: str           # "22621.5039"
    os_type: str         # "client" or "server"
    major_version: int   # 10, 11, 2022, 2025
    windows_version: str # "22H2"
    release_date: str    # "2026-05-13"
    kb_article: str      # "KB5058411"
    release_type: str    # "Standard", "Preview", "Out-of-band", "Hotpatch", "Hotpatch-OOB"
    is_expired: bool
    article_url: str | None
