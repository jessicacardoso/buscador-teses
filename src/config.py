from loguru import logger
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

logger.add(
    "logs/info.log",
    level="INFO",
    rotation="10 MB",
    compression="zip",
    retention="10 days",
)
logger.add(
    "logs/error.log",
    level="ERROR",
    rotation="10 MB",
    compression="zip",
    retention="10 days",
)


class Settings(BaseSettings):
    CHROMA_CLIENT_AUTH_CREDENTIALS: SecretStr
    CHROMA_CLIENT_HOSTNAME: str
    CHROMA_CLIENT_PORT: int
    CHROMA_CLIENT_AUTH_PROVIDER: str

    MODEL_NAME_OR_PATH: str = "models/instructor"
    DEVICE: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

if __name__ == "__main__":
    print(settings.model_dump())
