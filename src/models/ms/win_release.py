from pydantic import BaseModel


class WinRelease(BaseModel):
    version: str       # base build number, e.g. "22621"
    full_version: str  # e.g. "10.0.22621"
    build: str         # marketing name, e.g. "22H2"
