"""Runtime-only mutations: prove W-13 assertions fail, without editing source files."""
import inspect
import json
import subprocess
import sys
import textwrap
from pathlib import Path


CASES = {
    "missing_roles": (
        "doc2roadmap.application.use_cases.build_document", "BuildDocument", "execute",
        "roles = self.pipeline.label_roles(doc_id)", "roles = {}",
        "tests/unit/application/test_build_document.py::test_runs_steps_in_order_preserves_metadata_and_records_usage_delta",
    ),
    "roles_after_canonical": (
        "doc2roadmap.application.use_cases.build_document", "BuildDocument", "execute",
        "roles = self.pipeline.label_roles(doc_id)\n                            a3 = self.pipeline.a3(doc_id)\n                            canonical = self.pipeline.canonical(doc_id, language)",
        "a3 = self.pipeline.a3(doc_id)\n                            canonical = self.pipeline.canonical(doc_id, language)\n                            roles = self.pipeline.label_roles(doc_id)",
        "tests/unit/application/test_build_document.py::test_runs_steps_in_order_preserves_metadata_and_records_usage_delta",
    ),
    "disabled_page_gates": (
        "doc2roadmap.application.use_cases.build_document", "BuildDocument", "execute",
        'metrics = self._check_pages(reading.get("page_texts", []), language)', "metrics = {}",
        "tests/unit/application/test_build_document.py::test_input_gates_reject_before_pipeline_steps",
    ),
    "wrong_transport": (
        "doc2roadmap.composition_build", "DocumentPipeline", "__init__",
        "transport=settings.llm_transport", 'transport="developer_api"',
        "tests/unit/application/test_build_pipeline.py::test_pipeline_passes_vertex_settings_to_generation_and_embedding",
    ),
}


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--case":
        import importlib
        import pytest
        name = sys.argv[2]
        module_name, cls, method, old, new, node = CASES[name]
        module = importlib.import_module(module_name)
        source = inspect.getsource(getattr(getattr(module, cls), method))
        assert old in source, "mutation no longer matches its target"
        namespace = {}
        exec(compile(textwrap.dedent(source.replace(old, new)), "<w13-mutation>", "exec"),
             module.__dict__, namespace)
        setattr(getattr(module, cls), method, namespace[method])
        result = pytest.main([node, "-q", "--tb=line", "-p", "no:cacheprovider",
                              "--basetemp=tmp/w13-mutation-" + name])
        sys.exit(0 if result == pytest.ExitCode.TESTS_FAILED else 1)
    root = Path(__file__).resolve().parents[1]
    output = root / "tmp/w13-mutations"
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    for name in CASES:
        result = subprocess.run([sys.executable, "-X", "utf8", __file__, "--case", name],
                                cwd=root, capture_output=True, text=True, encoding="utf-8")
        (output / (name + ".txt")).write_text(result.stdout + result.stderr, encoding="utf-8")
        row = {"mutation": name, "caught": result.returncode == 0}
        rows.append(row)
        print(json.dumps(row), flush=True)
    (output / "results.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    sys.exit(0 if all(row["caught"] for row in rows) else 1)


if __name__ == "__main__":
    main()
