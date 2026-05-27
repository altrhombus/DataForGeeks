from pydantic import BaseModel


class WinSku(BaseModel):
    value: str    # e.g. "PRODUCT_PROFESSIONAL"
    hex: str      # e.g. "0x00000030"
    dec: int      # decimal integer value
    meaning: str  # description of the edition
