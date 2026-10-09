from gerboise.config import Settings


def test_defaults(monkeypatch):
    monkeypatch.setenv("DISCORD_BOT_TOKEN", "tok")
    monkeypatch.setenv("API_KEY", "key")
    monkeypatch.delenv("DB_PATH", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)

    settings = Settings(_env_file=None)

    assert settings.db_path == "/data/gerboise.db"
    assert settings.log_level == "INFO"
    assert settings.discord_bot_token.get_secret_value() == "tok"
    assert settings.api_key.get_secret_value() == "key"


def test_overrides(monkeypatch):
    monkeypatch.setenv("DISCORD_BOT_TOKEN", "tok")
    monkeypatch.setenv("API_KEY", "key")
    monkeypatch.setenv("DB_PATH", "/tmp/custom.db")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    settings = Settings(_env_file=None)

    assert settings.db_path == "/tmp/custom.db"
    assert settings.log_level == "DEBUG"
