from pathlib import Path
from uuid import uuid4

from alembic.config import Config
from alembic.script import ScriptDirectory
import pytest
from sqlalchemy import inspect, text

from wayfinder.infrastructure.database import create_database_engine, upgrade_database


def test_w03_is_single_head_after_w02():
    config = Config()
    config.set_main_option("script_location", str(Path(__file__).parents[1] / "wayfinder/migrations"))
    scripts = ScriptDirectory.from_config(config)
    assert scripts.get_heads() == ["w03_0004"]
    assert scripts.get_revision("w03_0004").down_revision == "w02_0003"
    assert scripts.get_revision("w02_0003").down_revision == "w05_0002"


@pytest.mark.postgres
def test_upgrade_w02_to_w03_preserves_existing_accounts(empty_postgres_database_url):
    upgrade_database(empty_postgres_database_url, "w02_0003")
    engine = create_database_engine(empty_postgres_database_url)
    account_id = str(uuid4())
    try:
        with engine.begin() as connection:
            connection.execute(text("""INSERT INTO account
                (id,email,email_normalized,password_hash,display_name,created_at,updated_at)
                VALUES (:id,'migration@example.vn','migration@example.vn','existing-hash','Người học',now(),now())"""),
                {"id": account_id})
        upgrade_database(empty_postgres_database_url)
        assert "email_token" in inspect(engine).get_table_names()
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "w03_0004"
            assert connection.scalar(text("SELECT email FROM account WHERE id=:id"), {"id": account_id}) == "migration@example.vn"
            assert connection.scalar(text("SELECT count(*) FROM email_token")) == 0
    finally:
        engine.dispose()
