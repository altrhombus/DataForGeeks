from pydantic import BaseModel, ConfigDict


class BitlockerVolumeType(BaseModel):
    model_config = ConfigDict(frozen=True)

    volume_type_enum: int  # integer enum value
    description: str       # e.g. "operatingSystemVolume"
