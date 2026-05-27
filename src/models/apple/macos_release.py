from pydantic import BaseModel


class MacOsRelease(BaseModel):
    os_name: str        # "Sonoma"
    version: str        # "14.2.1"
    major_version: int  # 14
    release_date: str   # "2023-12-19"
