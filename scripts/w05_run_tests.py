"""Use local db-test credentials without placing secrets in shell commands/logs."""
import os
import subprocess
import sys
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy.engine import URL


root = Path(__file__).resolve().parents[1]
env = dict(os.environ)
if not env.get("WAYFINDER_TEST_DATABASE_URL"):
    configured = root / "src/web/.env"
    if not configured.is_file():
        configured = root.parents[1] / "src/web/.env"
    values = dotenv_values(configured)
    if values.get("WAYFINDER_TEST_DATABASE_URL"):
        env["WAYFINDER_TEST_DATABASE_URL"] = values["WAYFINDER_TEST_DATABASE_URL"]
    elif values.get("POSTGRES_TEST_PASSWORD"):
        url = URL.create("postgresql+psycopg", username="wayfinder", password=values["POSTGRES_TEST_PASSWORD"],
                         host="127.0.0.1", port=5433, database="wayfinder_test")
        env["WAYFINDER_TEST_DATABASE_URL"] = url.render_as_string(hide_password=False)
env["PYTHONPATH"] = os.pathsep.join([str(root / "src"), str(root / "src/web/backend")])
raise SystemExit(subprocess.call([sys.executable, "-X", "utf8", "-m", "pytest", *sys.argv[1:],
                                 "--require-postgres", "-p", "no:cacheprovider"], cwd=root, env=env))
