from pydantic import BaseModel, ConfigDict


class WinLifecycleServer(BaseModel):
    model_config = ConfigDict(frozen=True)

    version: str              # e.g. "Windows Server 2022"
    tier: str                 # e.g. "Windows Server 2022" or "Extended Security Update Year 1"
    start_date: str           # ISO 8601 date
    mainstream_end_date: str  # ISO 8601 date
    extended_end_date: str    # ISO 8601 date
