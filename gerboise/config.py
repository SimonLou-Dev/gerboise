from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    discord_bot_token: SecretStr
    api_key: SecretStr
    db_path: str = "/data/gerboise.db"
    log_level: str = "INFO"


settings = Settings()
