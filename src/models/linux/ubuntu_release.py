from pydantic import BaseModel, ConfigDict


class UbuntuRelease(BaseModel):
    model_config = ConfigDict(frozen=True)

    version: str        # "20.04"
    codename: str       # "Focal Fossa"
    series: str         # "focal"
    release_date: str   # "2020-04-23"
    status: str         # "Supported", "Obsolete", "Current Stable Release", "Active Development"
    is_lts: bool
    standard_support_end: str | None  # "2025-04-23" (computed from release_date + policy)
    esm_support_end: str | None       # "2030-04-23" (LTS only)
