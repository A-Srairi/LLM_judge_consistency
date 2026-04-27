from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    environment: str = "development"
    groq_api_key: str = ""
    database_url: str = ""
    redis_url: str = ""
    rate_limit_per_ip: int = 20
    default_n_samples: int = 2
    max_n_samples: int = 5

    default_judges: List[str] = [
        "groq/llama-3.3-70b-versatile",
        "groq/llama-3.1-8b-instant",
        "groq/qwen/qwen3-32b",
    ]

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