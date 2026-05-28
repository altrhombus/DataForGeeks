from pydantic import BaseModel, ConfigDict


class WinSku(BaseModel):
    model_config = ConfigDict(frozen=True)

    value: str    # e.g. "PRODUCT_PROFESSIONAL"
    hex: str      # e.g. "0x00000030"
    dec: int      # decimal integer value
    meaning: str  # description of the edition
