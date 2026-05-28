from pydantic import BaseModel, ConfigDict


class M365Build(BaseModel):
    model_config = ConfigDict(frozen=True)

    release_date: str  # ISO 8601 date
    channel: str       # e.g. "Current", "Monthly Enterprise"
    build: str         # e.g. "19929.20164"
    version: str       # e.g. "2604"
    full_build: str    # e.g. "16.0.19929.20164"
