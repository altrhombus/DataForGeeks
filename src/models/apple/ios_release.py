from pydantic import BaseModel, ConfigDict


class IosRelease(BaseModel):
    model_config = ConfigDict(frozen=True)

    product: str        # "iOS" or "iPadOS"
    version: str        # "17.2.1"
    major_version: int  # 17
    release_date: str   # "2023-12-19"
