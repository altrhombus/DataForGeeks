from pydantic import BaseModel


class Locale(BaseModel):
    lang_code: int      # decimal LCID, e.g. 1033
    lang_code_hex: str  # 4-char hex, e.g. "0409"
    lang_name: str      # e.g. "English - United States"
    lang_tag: str       # IETF BCP 47, e.g. "en-US"
