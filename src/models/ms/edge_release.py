from pydantic import BaseModel


class EdgeRelease(BaseModel):
    version: str        # "148.0.3967.54"
    major_version: int  # 148
    release_date: str   # "2026-05-07"
