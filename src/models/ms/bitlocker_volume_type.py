from pydantic import BaseModel


class BitlockerVolumeType(BaseModel):
    volume_type_enum: int  # integer enum value
    description: str       # e.g. "operatingSystemVolume"
