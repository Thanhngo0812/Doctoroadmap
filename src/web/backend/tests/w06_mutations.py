"""Sequential acceptance mutations; restore each production file in a finally block."""
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET


ROOT = Path(__file__).absolute().parents[4]
BASE = ROOT / "src/web/backend/wayfinder"
TESTS = "src/web/backend/tests/test_courses_w06.py::"


def run_mutation(label, relative, before, after, test):
    source = BASE / relative
    original = source.read_bytes()
    needle, replacement = before.encode(), after.encode()
    assert needle in original, label
    folder = ROOT / "report/w06-evidence"
    folder.mkdir(exist_ok=True)
    xml = folder / f"{label}-red.xml"
    try:
        source.write_bytes(original.replace(needle, replacement))
        with (folder / f"{label}-red.log").open("w", encoding="utf-8") as log:
            result = subprocess.run([sys.executable, "scripts/w05_run_tests.py", TESTS + test,
                "-o", "addopts=", "-q", "--tb=short", f"--basetemp=tmp/w06-mutation-{label}",
                f"--junitxml={xml}"], cwd=ROOT, stdout=log, stderr=log)
        failures = list(ET.parse(xml).getroot().iter("failure"))
        errors = list(ET.parse(xml).getroot().iter("error"))
        assert result.returncode == 1 and failures and not errors, (label, result.returncode)
        return {"label": label, "exit_code": result.returncode, "assertion_failures": len(failures),
                "setup_errors": len(errors), "source_restored": True}
    finally:
        source.write_bytes(original)


def main():
    results = []
    for mutation in [
        ("route", "api/courses.py", "    return router", "    @router.get('/{cid}/unguarded-mutation')\n"
         "    def unguarded(cid: str):\n        return {'leaked': cid}\n\n    return router",
         "test_every_cid_route_hides_private_course_from_outsiders_including_admin"),
        ("gateway", "application/learning_gateway.py",
         'course, _ = self.courses.require_course(actor, cid, action="learn")',
         'course = self.courses.store.get_course(cid)',
         "test_every_cid_route_hides_private_course_from_outsiders_including_admin"),
        ("owner", "application/learning_gateway.py", 'SimpleNamespace(owner=actor.user_id,',
         'SimpleNamespace(owner=_untrusted.get("owner", actor.user_id),',
         "test_gateway_ignores_claimed_owner_and_records_actor_in_independent_postgres_connection"),
        ("store", "infrastructure/learning_runtime.py", 'DailySpendGuard(store,',
         'DailySpendGuard(__import__("doc2roadmap.infrastructure.artifacts.phase_b_store", '
         'fromlist=["InMemoryPhaseBStore"]).InMemoryPhaseBStore(),',
         "test_composition_binds_vertex_models_and_all_child_stores_to_postgres"),
        ("transport", "composition.py", 'transport="vertex",', 'transport="developer_api",',
         "test_composition_binds_vertex_models_and_all_child_stores_to_postgres"),
    ]:
        results.append(run_mutation(*mutation))
    (ROOT / "report/w06-evidence/mutations.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
