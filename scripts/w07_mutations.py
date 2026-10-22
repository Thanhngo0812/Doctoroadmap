"""Run W-07 guards against broken variants, sequentially, then restore source bytes."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "report/w07-evidence"
GATEWAY = "src/web/backend/wayfinder/application/learning_gateway.py"
PROGRESS = "src/doc2roadmap/application/phase_b/progress.py"
W07 = "src/web/backend/tests/test_learning_progress_w07.py::"
W06 = "src/web/backend/tests/test_courses_w06.py::"


def run_case(label, relative, transform, test):
    source = ROOT / relative
    original = source.read_bytes()
    changed = transform(original.decode("utf-8").replace("\r\n", "\n")).encode("utf-8")
    assert changed != original, f"mutation did not change source: {label}"
    stamp = __import__("uuid").uuid4().hex[:8]
    xml = OUTPUT / f"mutation-{label}-red.xml"
    command = [sys.executable, "scripts/w05_run_tests.py", test, "-o", "addopts=", "-q", "--tb=short", "--assert=plain",
               f"--basetemp=tmp/w07-mutation-{label}-{stamp}", f"--junitxml={xml}"]
    try:
        source.write_bytes(changed)
        with (OUTPUT / f"mutation-{label}-red.log").open("w", encoding="utf-8") as log:
            result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=log)
        tree = ET.parse(xml)
        failures, errors = list(tree.iter("failure")), list(tree.iter("error"))
        assert result.returncode == 1 and failures and not errors, (label, result.returncode, len(failures), len(errors))
        record = {"label": label, "command": command, "native_exit_code": result.returncode,
                  "assertion_failures": len(failures), "setup_errors": len(errors),
                  "source_sha256": hashlib.sha256(original).hexdigest()}
    finally:
        source.write_bytes(original)
        assert source.read_bytes() == original, f"source was not restored: {label}"
    return {**record, "source_restored": True}


def replace_once(before, after):
    def transform(source):
        assert source.count(before) == 1, before
        return source.replace(before, after, 1)
    return transform


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    cases = [
        ("route-inventory", "src/web/backend/wayfinder/api/courses.py", replace_once(
            "    return router", "    @router.get('/{cid}/unguarded-w07-mutation')\n"
            "    def unguarded(cid: str):\n        return {'leaked': cid}\n\n    return router"),
         W06 + "test_every_cid_route_hides_private_course_from_outsiders_including_admin"),
        ("membership", GATEWAY, replace_once(
            'course, _ = self.courses.require_course(actor, cid, action="learn")',
            'course = self.courses.store.get_course(cid)'),
         W06 + "test_every_cid_route_hides_private_course_from_outsiders_including_admin"),
        ("actor-owner", GATEWAY, replace_once(
            ".set_progress(actor.user_id, course.doc_id, node_id, learned)",
            ".set_progress(course.owner_id, course.doc_id, node_id, learned)"),
         W07 + "test_progress_is_isolated_between_members_using_independent_postgres_runtimes"),
        ("progress-reader", GATEWAY, replace_once(
            "result = self.runtime.progress(graph).get_progress(actor.user_id, course.doc_id)",
            "result = self.runtime.progress(graph).get_progress(course.owner_id, course.doc_id)"),
         W07 + "test_progress_is_isolated_between_members_using_independent_postgres_runtimes"),
        ("published-node", "src/web/backend/wayfinder/api/courses.py", replace_once(
            "learning.set_progress(actor, cid, node_id, data.learned)",
            'learning.set_progress(actor, cid, "a", data.learned)'),
         W07 + "test_progress_http_validates_node_and_boolean_and_hides_private_course"),
        ("learner-precedence", PROGRESS, replace_once(
            'if existing and existing.get("source") == "learner":', 'if False:'),
         W07 + "test_unmark_then_correct_quiz_keeps_learner_choice_through_gateway"),
        ("strict-boolean", "src/web/backend/wayfinder/api/courses.py", replace_once(
            "learned: bool = Field(strict=True)", "learned: bool"),
         W07 + "test_progress_http_validates_node_and_boolean_and_hides_private_course"),
        ("quiz-atomic", PROGRESS, replace_once(
            '            with self.store.atomic():\n                existing =',
            '            with __import__("contextlib").nullcontext():\n                existing ='),
         W07 + "test_quiz_read_then_concurrent_learner_unmark_is_serialized_by_postgres"),
    ]
    selected = set(sys.argv[1:])
    assert selected <= {case[0] for case in cases}, "unknown mutation label"
    results_path = OUTPUT / "mutations.json"
    results = ([row for row in json.loads(results_path.read_text(encoding="utf-8"))
                if row["label"] not in selected] if selected and results_path.exists() else [])
    try:
        for args in cases:
            if selected and args[0] not in selected:
                continue
            record = run_case(*args)
            results.append(record)
            print(json.dumps(record), flush=True)
    finally:
        (OUTPUT / "mutations.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
