from pydantic import BaseModel


class WinLifecycleClient(BaseModel):
    version: str    # e.g. "22H2"
    sku: str        # e.g. "Windows 11 Home and Pro"
    start_date: str # ISO 8601 date
    end_date: str   # ISO 8601 date
