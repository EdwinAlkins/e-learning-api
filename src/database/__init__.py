import logging
from typing import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base

from src.config import settings


logger = logging.getLogger("Database")

logger.info("Connecting to database ...")
# Chemin vers le fichier de base de données SQLite
db_path = Path(settings.DATABASE_PATH)
db_path.parent.mkdir(parents=True, exist_ok=True)

SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"
# SQLite nécessite check_same_thread=False pour FastAPI
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=settings.DEBUG,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
logger.info("Database connected !")

BaseModel = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
