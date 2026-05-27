from pydantic import BaseModel


class ExchangeBuildNumber(BaseModel):
    product_name: str      # "Exchange Server SE RTM May26HU"
    exchange_version: str  # "SE", "2019", "2016", "2013"
    build: str             # "15.2.2562.41"
    build_long: str        # "15.02.2562.041"
    release_date: str      # "2026-05-07"
