from pydantic import BaseModel, ConfigDict


class EdgeRelease(BaseModel):
    model_config = ConfigDict(frozen=True)

    version: str        # "148.0.3967.54"
    major_version: int  # 148
    release_date: str   # "2026-05-07"
