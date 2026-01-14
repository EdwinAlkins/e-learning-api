from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    debug: bool = False
    DATABASE_PATH: str = "database.db"
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False

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
