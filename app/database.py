from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.config import get_settings


def get_engine() -> Engine:
    settings = get_settings()
    connect_args = {}
    if settings.database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False, "timeout": 10}
    return create_engine(settings.database_url, connect_args=connect_args, future=True)


def ping_database() -> bool:
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return True
