from pydantic import BaseModel


class SqlBuildNumber(BaseModel):
    sql_version: str       # "SQL Server 2022"
    major_version: int     # 2022
    build: str             # "16.0.4185.3"
    service_pack: str | None
    update_type: str       # "CU5", "GDR", "RTM", "CU4 + GDR"
    kb_article: str | None # "KB5084896"
    release_date: str      # "2026-05-20"
    article_url: str | None
