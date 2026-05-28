from pydantic import BaseModel, ConfigDict


class AndroidRelease(BaseModel):
    model_config = ConfigDict(frozen=True)

    version: str        # "15"
    api_level: int      # 35
    release_date: str   # "2024-06-01" (day normalised to 01; source has month/year only)
