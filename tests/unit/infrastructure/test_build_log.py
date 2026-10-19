import json
import sqlite3

import pytest

from doc2roadmap.application.ports.build import BuildResult
from doc2roadmap.infrastructure.artifacts.build_log import SqliteBuildLog


@pytest.mark.parametrize("status", ["succeeded", "failed", "cancelled", "rejected", "dry_run"])
def test_terminal_build_usage_is_committed_and_readable_from_another_connection(tmp_path, status):
    path = tmp_path / "nested" / "builds.sqlite3"
    recorder = SqliteBuildLog(path)
    result = BuildResult("u-123", status, "abc123:cfg", graph_version=12,
                         spent_usd=.0123, model_calls=3, input_tokens=420,
                         output_tokens=110, usage_complete=False, elapsed_seconds=2.5)
    recorder(result)
    with sqlite3.connect(path) as connection:
        row = connection.execute(
            "SELECT doc_id, status, spent_usd, model_calls, usage_complete, result_json "
            "FROM build_runs"
        ).fetchone()
    assert row[:5] == ("u-123", status, .0123, 3, 0)
    stored = json.loads(row[5])
    assert stored["pipeline_version"] == "abc123:cfg"
    assert stored["input_tokens"] == 420
    assert stored["graph_version"] == 12
    assert not any("estimate" in key for key in stored)


def test_repeated_attempts_are_separate_database_rows(tmp_path):
    path = tmp_path / "builds.sqlite3"
    recorder = SqliteBuildLog(path)
    recorder(BuildResult("u-123", "failed", "v1", spent_usd=.01))
    recorder(BuildResult("u-123", "succeeded", "v1", spent_usd=.02))
    with sqlite3.connect(path) as connection:
        count, total = connection.execute("SELECT COUNT(*), SUM(spent_usd) FROM build_runs").fetchone()
    assert count == 2
    assert total == pytest.approx(.03)


def test_failed_build_records_priced_generation_and_embedding_usage(tmp_path):
    from pathlib import Path
    from doc2roadmap.application import stage_measurements
    from doc2roadmap.application.build_usage import BuildUsage
    from doc2roadmap.application.use_cases.build_document import BuildDocument
    from tests.unit.application.test_build_document import FakePipeline

    class MeasuredPipeline(FakePipeline):
        def __init__(self):
            super().__init__()
            self.meter = BuildUsage()

        def usage(self):
            return self.meter.snapshot()

        def label_roles(self, doc_id):
            with self.meter.capture("gemini-3.1-flash-lite"):
                stage_measurements.record_model_call()
                stage_measurements.record_usage({"promptTokenCount": 100, "candidatesTokenCount": 20})
            return {}

        def a3(self, doc_id):
            with self.meter.capture("gemini-embedding-001:768"):
                stage_measurements.record_model_call(embedding=True)
                stage_measurements.record_usage({"promptTokenCount": 50}, embedding=True)
            return {}

        def roadmap(self, doc_id):
            with self.meter.capture("gemini-3.1-flash-lite"):
                stage_measurements.record_model_call()
                stage_measurements.record_usage({"promptTokenCount": 200, "candidatesTokenCount": 50})
                raise TimeoutError("failure after a billed response")

    path = tmp_path / "builds.sqlite3"
    result = BuildDocument(MeasuredPipeline(), "v1", recorder=SqliteBuildLog(path)).execute(Path("x"), "d")
    assert result.status == "failed"
    with sqlite3.connect(path) as connection:
        usd, calls, stored = connection.execute("SELECT spent_usd, model_calls, result_json FROM build_runs").fetchone()
    assert usd == pytest.approx(.0001875)
    assert calls == 3
    assert json.loads(stored)["input_tokens"] == 350
    assert json.loads(stored)["output_tokens"] == 70
    assert json.loads(stored)["usage_complete"] is True
