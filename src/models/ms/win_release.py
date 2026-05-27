from pydantic import BaseModel


class WinRelease(BaseModel):
    os_type: str         # "client"
    major_version: int   # 10 or 11
    windows_version: str # "22H2"
    os_build: str        # "22621"
    full_version: str    # "10.0.22621"
