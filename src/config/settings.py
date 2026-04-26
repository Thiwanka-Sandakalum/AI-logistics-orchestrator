"""Configuration management for the assistant service."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration from environment variables."""

    # Data Backend
    data_backend: str = "sqlite"  # "sqlite" or "api"
    sqlite_db_path: str = "./data/assistant.db"
    seed_demo_data: bool = False

    # Existing API Configuration
    existing_api_base_url: str = "http://localhost:8080"
    existing_api_timeout: int = 30
    existing_api_max_retries: int = 3

    # Model Configuration
    model_id: str = "gemini-2.5-flash"
    model_temperature: float = 0.1
    model_max_tokens: int = 2048


# Load settings
settings = Settings()  # type: ignore
