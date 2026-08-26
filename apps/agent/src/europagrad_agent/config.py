"""Environment-driven settings for the agent (task 1 scaffold; extended by tasks 6-11)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    supabase_url: str = ""
    supabase_service_key: str = ""
    openrouter_api_key: str = ""
    openrouter_model: str = "google/gemini-2.0-flash-001"
    tavily_api_key: str = ""
    jina_api_key: str = ""
    github_token: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
