from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    BOT_TOKEN: str = "test_token"
    POSTGRES_DSN: str = "postgresql+asyncpg://test:test@localhost:5432/test"
    REDIS_DSN: str = "redis://localhost:6379/0"

    REMINDER_CHECK_INTERVAL: int = 30
    DEFAULT_REMINDER_OFFSET: int = 15

    LOG_LEVEL: str = "INFO"


settings = Settings()