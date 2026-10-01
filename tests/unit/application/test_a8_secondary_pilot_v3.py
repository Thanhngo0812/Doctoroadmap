import importlib.util
from pathlib import Path


def test_pilot_filters_to_gold_targets_and_writes_only_to_evaluation_store(monkeypatch):
    scripts = Path(__file__).resolve().parents[3] / "scripts/doc-lo-trinh"
    monkeypatch.syspath_prepend(str(scripts))
    spec = importlib.util.spec_from_file_location("a8_secondary_pilot_v3", scripts / "chay_a8_secondary_pilot_v3.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    nodes = [{"node_id": name, "cluster_id": "g"} for name in ("a", "b", "c")]
    pairs = [{"pair_id": name, "left": left, "right": right}
             for name, left, right in (("ab", "a", "b"), ("ac", "a", "c"))]
    payload = {"nodes": nodes, "suspected_pairs": pairs, "pair_cluster_ledger": [],
               "main_edges": [], "routing": {"route": "chapter"}, "identity_map": {"alias": "a"}}
    assert module.pilot_pairs(payload, {"alias", "b"}) == pairs[:1]

    class Store:
        def __init__(self):
            self.saved = []

        def find_graph(self, *args):
            return None

        def save_graph(self, *args):
            self.saved.append(args)

        def load_checkpoint(self, *args):
            return None

        def save_checkpoint(self, *args):
            self.saved.append(args)

        def clear_checkpoint(self, *args):
            pass

    base, output = Store(), Store()
    evaluation = module.EvaluationStore(base, output)
    evaluation.save_checkpoint("doc-1", "pilot", {"completed": 1})
    assert output.saved == [("doc-1", "pilot", {"completed": 1})]
    assert base.saved == []
