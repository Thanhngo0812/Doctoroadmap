import json
from types import SimpleNamespace

import pytest

from doc2roadmap.application.use_cases.judge_identity import JudgeIdentity
from tests.unit.application.test_judge_identity import Store, node


class TwoPassModel:
    model_id = "fixture-model"

    def __init__(self, relation="dong_nhat", verdict="same"):
        self.relation, self.verdict, self.calls = relation, verdict, []

    def start_session(self, system_prompt):
        model = self

        class Session:
            def ask_json(self, prompt, *, response_schema):
                data = json.loads(prompt.split("\nCorrect this validation error:")[0])
                verifying = "relation" in response_schema["properties"]
                model.calls.append((verifying, data))
                payload = {"pair_id": data["pair_id"], "reason": "independent" if verifying else "FIRST-PASS-SECRET"}
                payload["relation" if verifying else "verdict"] = model.relation if verifying else model.verdict
                return SimpleNamespace(payload=payload, usage=None)
        return Session()


def pair_store():
    store = Store()
    store.teaching.payload["nodes"] = [node("csdl", "CSDL", 1, status="mentioned_only"),
        node("database", "Cơ sở dữ liệu", 20)]
    store.teaching.payload["nodes"][0]["aliases"] = [{"name": "Database", "evidence": {"chunk_id": "c"}}]
    store.teaching.payload["requires_edges"] = []
    return store


@pytest.mark.parametrize("relation,verdict,review,merged,verify_calls", [
    ("truong_hop_rieng", "same", None, False, 1),
    ("dong_nhat", "same", None, True, 1),
    ("truong_hop_rieng", "same", "Đồng ý gộp", True, 1),
    ("dong_nhat", "different", None, False, 0),
    ("khac", "different", "Đồng ý gộp", True, 0),
    ("dong_nhat", "same", "Không gộp", False, 1),
])
def test_independent_verification_and_human_override(relation, verdict, review, merged, verify_calls):
    store, model = pair_store(), TwoPassModel(relation, verdict)
    original = json.dumps(store.teaching.payload, sort_keys=True)
    reviews = {frozenset(("csdl", "database")): review} if review else {}
    uc = JudgeIdentity(store, model, review=reviews)
    artifact, _ = uc.execute("doc", upstream=store.teaching)
    assert artifact.payload["identity_map"] == ({"csdl": "database"} if merged else {})
    calls = [data for verify, data in model.calls if verify]
    assert len(calls) == verify_calls
    for data in calls:
        assert set(data) == {"pair_id", "first", "second"}
        assert "FIRST-PASS-SECRET" not in json.dumps(data)
        assert set(data["first"]) == {"name", "aliases", "description", "anchor_sentence"}
    row = artifact.payload["identity_log"][0]
    assert row["model_verdict"] == verdict
    assert row["verify_relation"] == (relation if verify_calls else None)
    assert row["verdict"] == ("same" if merged else "different")
    if merged:
        head = artifact.payload["nodes"][0]
        assert head["teaching_status"] == "taught" and head["teaching_order_index"] == 20
        assert {a["name"] for a in head["aliases"]} == {"CSDL", "Database"}
        assert all(a["source"] == "identity" for a in head["aliases"])
    assert json.dumps(store.teaching.payload, sort_keys=True) == original
    assert uc.plan("doc", upstream=store.teaching).calls_estimate == 0
    before = len(model.calls)
    uc.execute("doc", upstream=store.teaching)
    assert len(model.calls) == before  # cả hai checkpoint được tiếp tục, không hỏi lại


def test_verification_failure_never_merges_and_is_reported_as_open():
    store = pair_store()
    artifact, _ = JudgeIdentity(store, TwoPassModel("not-a-relation")).execute("doc", upstream=store.teaching)
    assert artifact.payload["identity_map"] == {}
    assert artifact.payload["identity_open_pairs"] == ["p1"]


def test_existing_first_pass_checkpoint_survives_verify_prompt_change(monkeypatch):
    from doc2roadmap.application.use_cases import judge_identity as module

    store, model = pair_store(), TwoPassModel()
    uc = JudgeIdentity(store, model)
    uc.execute("doc", upstream=store.teaching)
    first_key = next(k for k in store.checkpoints if k.startswith("identity-") and not k.startswith("identity-verify-"))
    first_checkpoint = json.dumps(store.checkpoints[first_key], sort_keys=True)
    load = module.load_prompt
    monkeypatch.setattr(module, "load_prompt", lambda phase, name: load(phase, name) + ("\nchanged" if name == "identity_verify" else ""))
    before = len(model.calls)
    plan = uc.plan("doc", upstream=store.teaching)
    assert plan.calls_estimate == 1
    uc.execute("doc", upstream=store.teaching)
    assert [v for v, _ in model.calls[before:]] == [True]
    assert json.dumps(store.checkpoints[first_key], sort_keys=True) == first_checkpoint
