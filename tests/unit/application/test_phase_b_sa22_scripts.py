"""Guards for the SA-22 evaluation scripts (scripts/phase-b/sa22_*.py). No network, no shared artifacts."""
import json
import re
import sys
from pathlib import Path
from urllib.request import Request

import pytest

SCRIPTS = Path(__file__).resolve().parents[3] / "scripts" / "phase-b"
QUIZ = Path(__file__).resolve().parents[3] / "src" / "doc2roadmap" / "application" / "phase_b" / "quiz.py"
sys.path.insert(0, str(SCRIPTS))

import sa22_metrics  # noqa: E402
import sa22_run  # noqa: E402
from sa22_common import Capturing  # noqa: E402


def test_every_rejection_reason_in_quiz_py_is_mapped_to_a_rule():
    source = QUIZ.read_text(encoding="utf-8")
    reasons = set(re.findall(r'"((?:local|normalize)\.[a-z_]+)"', source))
    assert len(reasons) >= 2  # the scan really found the reasons (quiz-3 keeps only the cloze ones and the repeat check here)
    unmapped = reasons - set(sa22_metrics.RULE_OF) - {"local.variant_cap", "local.repeated_question"}
    assert not unmapped, f"rejection reasons without a Q rule: {sorted(unmapped)}"


def test_quiz_py_no_longer_has_quiz_2_verifier_reasons():
    # quiz-3 judges with a blind solver (quiz_context3.verdicts, reasons "solver.*"); VERIFIER_REASONS stays for the SA-22 runs.
    source = QUIZ.read_text(encoding="utf-8")
    assert not re.findall(r'"(verifier\.[a-z_]+)"', source)


def test_capturing_keeps_a_deep_copy_of_the_rejected_item_and_the_raw_of_a_normalize_failure():
    use = Capturing(graph=type("G", (), {"new_source_registry": lambda self: None})(), store=None)
    item = {"item_id": "qi_1", "stem": "Câu?", "options": [{"text": "a", "is_correct": True}, {"text": "b", "is_correct": False}],
            "evidence": [{"page": 3, "quote": "q"}]}
    concept = {"node_id": "n1", "name": "Khái niệm"}
    use._record_rejection("verifier", "verifier.wrong_choice", concept, {}, item)
    item["options"][0]["text"] = "changed afterwards"
    use._record_rejection("normalize", "normalize.option_count", concept, {"stem": "raw stem"})
    first, second = use.captured
    assert first["item"]["options"][0]["text"] == "a" and first["item"]["evidence"][0]["page"] == 3
    assert second["item"] is None and second["raw"] == {"stem": "raw stem"}
    assert len(use.diagnostics) == 2  # the product's own diagnostics still work


def test_hard_gate_refuses_the_attempt_after_the_limit_and_the_reserved_cap():
    body = json.dumps({"generationConfig": {"maxOutputTokens": 100}}).encode()
    gate = sa22_run.HardGate(cap=10.0, max_attempts=2)
    gate.reserve_request(Request("https://example.invalid", data=body))
    gate.reserve_request(Request("https://example.invalid", data=body))
    with pytest.raises(PermissionError, match="attempt limit"):
        gate.reserve_request(Request("https://example.invalid", data=body))
    tight = sa22_run.HardGate(cap=1e-9, max_attempts=100)
    with pytest.raises(PermissionError, match="hard cap"):
        tight.reserve_request(Request("https://example.invalid", data=body))
    assert tight.attempts == 0


def test_percentile_is_nearest_rank_and_empty_safe():
    assert sa22_metrics.percentile([], .5) is None
    assert sa22_metrics.percentile([10, 20, 30, 40, 50], .5) == 30
    assert sa22_metrics.percentile(list(range(1, 101)), .95) == 95
