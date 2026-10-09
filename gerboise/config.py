from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    discord_bot_token: SecretStr
    api_key: SecretStr
    db_path: str = "/data/gerboise.db"
    log_level: str = "INFO"
    # Si renseigné, les commandes slash sont synchronisées sur cette guild (instantané,
    # pratique pour un déploiement mono-serveur). Sinon, sync globale (propagation ~1h).
    discord_guild_id: str | None = None


settings = Settings()
