from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://movie:movie@localhost:5432/movie_reservation"
    secret_key: str = "dev-secret-change-in-production"
    access_token_expire_minutes: int = 60 * 24 * 7
    # Optional: seed refreshes posters from TMDB API when set (v3 key).
    tmdb_api_key: str | None = None


settings = Settings()
