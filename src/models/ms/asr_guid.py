from pydantic import BaseModel


class AsrGuid(BaseModel):
    asr_name: str  # human-readable rule name
    asr_guid: str  # rule GUID used in policy configuration
