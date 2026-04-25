from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    # environment
    environment: str = "development"

    # groq (default free judge)
    groq_api_key: str = ""

    # database
    database_url: str = "postgresql+asyncpg://dev:dev@localhost:5432/judge_auditor"

    # redis
    redis_url: str = "redis://localhost:6379"

    # rate limiting
    rate_limit_per_ip: int = 20

    # audit defaults
    default_n_samples: int = 10
    max_n_samples: int = 20

    # available judge models — free groq models by default
    default_judges: List[str] = [
        "groq/llama-3.3-70b-versatile",
        "groq/llama-3.1-8b-instant",
        "groq/qwen/qwen3-32b",
    ]

    # criteria used for evaluation
    default_criteria: List[str] = [
        "accuracy",
        "helpfulness",
        "conciseness",
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()