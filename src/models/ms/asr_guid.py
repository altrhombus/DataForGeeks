from pydantic import BaseModel, ConfigDict


class AsrGuid(BaseModel):
    model_config = ConfigDict(frozen=True)

    asr_name: str  # human-readable rule name
    asr_guid: str  # rule GUID used in policy configuration
