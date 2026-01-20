from pydantic_settings import BaseSettings
from pydantic import ConfigDict, Field


class Settings(BaseSettings):
    DATABASE_PATH: str = "database.db"
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False
    VIDEOS_PATH: str = "videos/"
    CATALOG_CACHE_PATH: str = "catalog_cache.json"
    CORS_ORIGINS: list[str] = Field(default=["*"])

    model_config = ConfigDict(
        # Charge d'abord .env.template, puis .env, puis les variables d'environnement
        env_file=[".env.template", ".env"],
        env_file_encoding="utf-8",
        case_sensitive=False,
        # Ignore les champs supplémentaires dans le .env
        extra="ignore",
    )


# Instance globale des paramètres
settings = Settings()
