"""Local CLI build ledger; web workers can inject a PostgreSQL recorder instead."""
import json
import sqlite3
from pathlib import Path
from uuid import uuid4

from doc2roadmap.application.ports.build import BuildResult


class SqliteBuildLog:
    def __init__(self, path: Path):
        self.path = Path(path)

    def __call__(self, result: BuildResult) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS build_runs (
                    id TEXT PRIMARY KEY,
                    doc_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    pipeline_version TEXT NOT NULL,
                    graph_version INTEGER,
                    spent_usd REAL NOT NULL,
                    model_calls INTEGER NOT NULL,
                    usage_complete INTEGER NOT NULL,
                    elapsed_seconds REAL NOT NULL,
                    recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    result_json TEXT NOT NULL
                )
            """)
            connection.execute("""
                INSERT INTO build_runs
                    (id, doc_id, status, pipeline_version, graph_version, spent_usd,
                     model_calls, usage_complete, elapsed_seconds, result_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (uuid4().hex, result.doc_id, result.status, result.pipeline_version,
                  result.graph_version, result.spent_usd, result.model_calls,
                  int(result.usage_complete), result.elapsed_seconds,
                  json.dumps(result.to_dict(), ensure_ascii=False)))
