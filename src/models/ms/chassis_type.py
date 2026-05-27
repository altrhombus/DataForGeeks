from pydantic import BaseModel


class ChassisType(BaseModel):
    value: str  # e.g. "Notebook", "Desktop"
    number: int # integer value returned by WMI
