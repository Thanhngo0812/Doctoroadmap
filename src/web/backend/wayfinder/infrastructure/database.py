"""PostgreSQL connections and programmatic Alembic migrations."""
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import SQLAlchemyError


def create_database_engine(database_url: str | URL) -> Engine:
    url = make_url(database_url)
    if url.get_backend_name() != "postgresql":
        raise ValueError("WayFinder requires a PostgreSQL database URL")
    url = url.set(drivername="postgresql+psycopg")
    return create_engine(url, pool_pre_ping=True, hide_parameters=True, connect_args={"connect_timeout": 3})


class DatabaseHealth:
    def __init__(self, database_url: str | URL):
        self.engine = create_database_engine(database_url)

    def __call__(self) -> str:
        try:
            with self.engine.connect() as connection:
                connection.execute(text("select 1"))
            return "ok"
        except SQLAlchemyError:
            return "down"

    def close(self) -> None:
        self.engine.dispose()


def upgrade_database(database_url: str | URL, revision: str = "head") -> None:
    # Alembic documents Config.attributes for sharing an existing connection:
    # https://alembic.sqlalchemy.org/en/latest/api/config.html
    config = Config()
    config.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "migrations"))
    engine = create_database_engine(database_url)
    try:
        with engine.begin() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, revision)
    finally:
        engine.dispose()
