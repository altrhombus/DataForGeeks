from pydantic import BaseModel, ConfigDict


class ChassisType(BaseModel):
    model_config = ConfigDict(frozen=True)

    value: str  # e.g. "Notebook", "Desktop"
    number: int # integer value returned by WMI
