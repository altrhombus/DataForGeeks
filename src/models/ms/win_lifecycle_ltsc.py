from pydantic import BaseModel


class WinLifecycleLtsc(BaseModel):
    version: str              # e.g. "2021 (21H2)"
    servicing_option: str     # e.g. "Long-Term Servicing Channel (LTSC)"
    build: str                # major build number, e.g. "19044"
    start_date: str           # ISO 8601 date
    mainstream_end_date: str  # ISO 8601 date or "End of updates"
    extended_end_date: str    # ISO 8601 date
