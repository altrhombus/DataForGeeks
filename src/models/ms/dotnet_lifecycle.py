from pydantic import BaseModel, ConfigDict


class DotnetLifecycle(BaseModel):
    model_config = ConfigDict(frozen=True)

    product: str           # ".NET Framework" or ".NET"
    version: str           # "4.8.1" or "9"
    release_date: str      # "2022-08-09"
    end_date: str | None   # "2027-01-12" or None (still supported)
