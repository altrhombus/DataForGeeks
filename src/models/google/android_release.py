from pydantic import BaseModel


class AndroidRelease(BaseModel):
    version: str        # "15"
    api_level: int      # 35
    release_date: str   # "2024-06-01" (day normalised to 01; source has month/year only)
