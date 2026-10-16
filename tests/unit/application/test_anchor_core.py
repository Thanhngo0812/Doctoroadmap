import copy
import json
from types import SimpleNamespace

import pytest

from doc2roadmap.application.anchor_core import AnchorCore


GENERATION = {"temperature": 0.0, "max_output_tokens": 2048}


def node(node_id="n", name="Cơ sở", **fields):
    return {"node_id": node_id, "name": name, "learnable": True, **fields}


def chunk(chunk_id="body", text="Cơ sở là một hệ độc lập sinh ra V.", **fields):
    return SimpleNamespace(chunk_id=chunk_id, text=text, order_index=10,
                           section_path=[], **fields)


class Model:
    model_id = "core-fixture"

    def __init__(self, *, status="defined_here", bad=None, confirmed=True):
        self.status, self.bad, self.confirmed, self.calls = status, bad, confirmed, []

    def start_session(self, prompt):
        return self

    def ask_json(self, prompt, *, response_schema):
        data = json.loads(prompt.split("\nCorrect this validation error:")[0])
        self.calls.append(data)
        if "explicit_prior" in response_schema["properties"]:
            assert set(data) == {"node_id", "concept", "quote"}
            assert "FIRST-VERDICT-SECRET" not in json.dumps(data)
            value = {"node_id": data["node_id"], "explicit_prior": self.confirmed, "reason": "independent check"}
        else:
            candidate = data["candidates"][0]
            value = {"node_id": data["node_id"], "status": self.status, "anchor": candidate["cand_id"],
                     "quote": candidate["sentence"], "reason": "FIRST-VERDICT-SECRET"}
            if self.bad == "anchor":
                value["anchor"] = "invented"
            elif self.bad == "quote":
                value["quote"] = "invented quotation"
            elif self.bad == "confidence":
                value["confidence"] = 1.0
        return SimpleNamespace(payload=value, usage={"promptTokenCount": 3, "candidatesTokenCount": 1,
                                                     "thoughtsTokenCount": 2, "totalTokenCount": 6})


def execute(core, model, **kwargs):
    answers, log, metrics = core.judge(model, generation=GENERATION, **kwargs)
    verified, prior_log, prior_metrics = core.verify_prior(model, answers, generation=GENERATION)
    checked, final = core.apply(answers, verified)
    metrics.update(prior_metrics)
    return checked, final, log, prior_log, metrics


def test_core_uses_caller_hard_mentions_and_returns_nodes_logs_tokens_without_artifacts():
    nodes = [node(defining_chunk_ids=["outline"])]
    original = copy.deepcopy(nodes)
    core = AnchorCore(nodes, [chunk("outline", "Cơ sở.", role="de_cuong"), chunk()], {"n": {"body"}})
    model = Model()
    checked, final, log, prior_log, metrics = execute(core, model)
    assert checked[0]["anchor"] == {"chunk_id": "body", "char_start": 0,
                                    "sentence": "Cơ sở là một hệ độc lập sinh ra V."}
    assert checked[0]["teaching_status"] == "taught"
    assert checked[0]["teaching_chunk_ids"] == ["body"] and checked[0]["teaching_order_index"] == 10
    assert checked[0]["defining_chunk_ids"] == ["outline"] and nodes == original
    assert final["n"]["status"] == "defined_here" and log[0]["valid"] is True and prior_log == []
    assert len(model.calls) == 1
    assert metrics == {"anchor_calls": 1, "anchor_input_tokens": 3, "anchor_output_tokens": 3,
                       "anchor_total_tokens": 6}


def test_core_no_candidates_does_not_call_model_and_preserves_media():
    nodes = [node("outside", "Số chiều"), node("missing", "Tên hoàn toàn vắng"),
             {"node_id": "media", "name": "Hình", "learnable": False}]
    core = AnchorCore(nodes, [chunk("outline", "Số chiều.", role="de_cuong")],
                      {"outside": {"outline"}})
    model = Model()
    checked, final, log, prior_log, metrics = execute(core, model)
    assert model.calls == [] and final == {} and log == [] and prior_log == [] and metrics == {}
    assert checked[0]["teaching_status"] == "mentioned_only" and checked[0]["mentioned_in"] == "de_cuong"
    assert checked[1]["teaching_status"] == "unchecked"
    assert checked[0]["anchor"] is None and checked[1]["teaching_chunk_ids"] == []
    assert checked[2] == nodes[2]


def test_core_retries_exact_name_scan_when_caller_has_no_candidate_chunks():
    core = AnchorCore([node()], [chunk()], {})
    model = Model()
    checked, _, _, _, _ = execute(core, model)
    assert len(model.calls) == 1 and checked[0]["teaching_chunk_ids"] == ["body"]


@pytest.mark.parametrize("bad", ["anchor", "quote", "confidence"])
def test_core_invalid_verdict_is_retried_then_kept_uncertain(bad):
    core = AnchorCore([node()], [chunk()], {"n": {"body"}})
    model = Model(bad=bad)
    checked, final, log, _, metrics = execute(core, model)
    assert len(model.calls) == 2 and metrics["anchor_calls"] == 2
    assert len(checked) == 1 and checked[0]["learnable"] is True
    assert checked[0]["teaching_status"] == "uncertain" and checked[0]["anchor"] is None
    assert final["n"]["reason"] == "invalid_response" and log[0]["valid"] is False


@pytest.mark.parametrize("confirmed,status,calls", [(True, "prior_knowledge", 2),
                                                  (False, "uncertain", 2), ("invalid", "uncertain", 3)])
def test_core_prior_knowledge_requires_independent_valid_confirmation(confirmed, status, calls):
    core = AnchorCore([node()], [chunk()], {"n": {"body"}})
    model = Model(status="prior_knowledge", confirmed=confirmed)
    checked, final, _, prior_log, metrics = execute(core, model)
    assert len(model.calls) == calls and metrics["anchor_prior_verify_calls"] == calls - 1
    assert checked[0]["teaching_status"] == status and checked[0]["anchor"] is None
    assert final["n"]["model_status"] == "prior_knowledge"
    assert final["n"]["prior_verification"]["explicit_prior"] is (confirmed if type(confirmed) is bool else None)
    assert prior_log[0]["valid"] is (type(confirmed) is bool)


def test_core_resumes_completed_answers_and_reuses_valid_decision_logs():
    core = AnchorCore([node()], [chunk()], {"n": {"body"}})
    model = Model()
    snapshots = []
    answers, log, metrics = core.judge(model, generation=GENERATION,
                                     save_checkpoint=lambda value: snapshots.append(copy.deepcopy(value)))
    assert snapshots == [{"answers": answers, "decision_log": log, "metrics": dict(metrics)}]
    resumed, resumed_log, resumed_metrics = core.judge(model, generation=GENERATION, **snapshots[0])
    assert resumed == answers and resumed_log == log and resumed_metrics == metrics and len(model.calls) == 1
    replayed, replay_log, replay_metrics = core.judge(model, generation=GENERATION, decision_log=log)
    assert replayed == answers and len(model.calls) == 1
    assert replay_log[-1]["reused"] is True and replay_metrics == {"anchor_reused": 1}


def test_core_prior_checkpoint_resumes_without_repeating_independent_verification():
    core = AnchorCore([node()], [chunk()], {"n": {"body"}})
    model = Model(status="prior_knowledge")
    answers, _, _ = core.judge(model, generation=GENERATION)
    snapshots = []
    verified, log, metrics = core.verify_prior(
        model, answers, generation=GENERATION,
        save_checkpoint=lambda value: snapshots.append(copy.deepcopy(value)))
    assert snapshots == [{"answers": verified, "decision_log": log, "metrics": dict(metrics)}]
    resumed, resumed_log, resumed_metrics = core.verify_prior(
        model, answers, generation=GENERATION, verified=snapshots[0]["answers"],
        decision_log=snapshots[0]["decision_log"], metrics=snapshots[0]["metrics"])
    assert resumed == verified and resumed_log == log and resumed_metrics == metrics
    assert len(model.calls) == 2
