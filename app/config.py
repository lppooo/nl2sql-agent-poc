from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    app_env: str = "dev"
    database_url: str = f"sqlite:///{PROJECT_ROOT / 'data' / 'agent_demo.db'}"
    sql_dialect: str = "sqlite"
    max_rows: int = 1000
    business_today: str = "2026-08-01"

    use_llm: bool = False
    llm_provider: str = "zhipu"
    llm_model: str = "glm-5-turbo"
    zhipu_api_key: str | None = None
    zhipu_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    allowed_tables: set[str] = Field(
        default_factory=lambda: {
            "users",
            "orders",
            "order_items",
            "products",
            "channels",
            "user_events",
        }
    )

    @property
    def llm_api_key(self) -> str | None:
        if self.llm_provider.lower() == "zhipu":
            return self.zhipu_api_key or self.openai_api_key
        return self.openai_api_key or self.zhipu_api_key

    @property
    def llm_base_url(self) -> str:
        if self.llm_provider.lower() == "zhipu":
            return self.zhipu_base_url
        return self.openai_base_url

    @property
    def llm_model_name(self) -> str:
        if self.llm_provider.lower() == "zhipu":
            return self.llm_model
        return self.openai_model

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
