from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str = Field(..., alias="BOT_TOKEN")
    channel_id: str = Field(..., alias="CHANNEL_ID")
    admin_chat_id: int = Field(..., alias="ADMIN_CHAT_ID")
    auto_publish: bool = Field(default=False, alias="AUTO_PUBLISH")
    sqlite_path: str = Field(default=str(BASE_DIR / "app" / "db" / "content.db"), alias="SQLITE_PATH")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")

    roman_post_hour: int = Field(default=9, alias="ROMAN_POST_HOUR")
    argument_post_hour: int = Field(default=18, alias="ARGUMENT_POST_HOUR")

    roman_dataset_path: str = Field(default=str(BASE_DIR / "app" / "data" / "roman_posts.csv"))
    argument_dataset_path: str = Field(default=str(BASE_DIR / "app" / "data" / "argument_topics.csv"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
