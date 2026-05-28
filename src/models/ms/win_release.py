from pydantic import BaseModel, ConfigDict


class WinRelease(BaseModel):
    model_config = ConfigDict(frozen=True)

    os_type: str         # "client"
    major_version: int   # 10 or 11
    windows_version: str # "22H2"
    os_build: str        # "22621"
    full_version: str    # "10.0.22621"
