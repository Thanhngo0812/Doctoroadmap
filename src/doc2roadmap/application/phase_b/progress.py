from __future__ import annotations

from doc2roadmap.application.phase_b.clock import SystemClock
from doc2roadmap.domain.phase_b_limits import context_hash


class ProgressUseCase:
    def __init__(self, store, graph, *, clock=None):
        self.store, self.graph = store, graph
        self.clock = clock or SystemClock()

    def _validate(self, owner, doc_id, node_id=None):
        if not owner:
            raise PermissionError("owner is required")
        if doc_id != self.graph.doc_id:
            raise ValueError("doc_id does not match graph")
        if node_id is not None and node_id not in self.graph.learnable_nodes:
            raise ValueError("unknown learnable node")

    def _key(self, owner, doc_id, node_id):
        return context_hash([owner, doc_id, node_id])

    def _write(self, owner, doc_id, node_id, learned, source):
        value = {"owner": owner, "doc_id": doc_id, "node_id": node_id,
                 "state": "learned" if learned else "not_learned", "source": source,
                 "updated_at": self.clock.now().isoformat()}
        self.store.put_record("progress", self._key(owner, doc_id, node_id), value)
        return value

    def set_progress(self, owner, doc_id, node_id, learned):
        self._validate(owner, doc_id, node_id)
        if not isinstance(learned, bool):
            raise ValueError("learned must be boolean")
        return self._write(owner, doc_id, node_id, learned, "learner")

    def mark_quiz_correct(self, owner, doc_id, node_ids):
        self._validate(owner, doc_id)
        for node_id in set(node_ids):
            self._validate(owner, doc_id, node_id)
            key = self._key(owner, doc_id, node_id)
            def update():
                existing = self.store.get_record("progress", key)
                if existing and existing.get("source") == "learner":
                    return existing
                return self._write(owner, doc_id, node_id, True, "quiz")
            # Serialize read/modify/write without caching a past progress value.
            self.store.single_flight("progress:" + key, update, cache_if=lambda _: False, negative_ttl_seconds=0)

    def get_progress(self, owner, doc_id):
        self._validate(owner, doc_id)
        records = {row["node_id"]: row for row in self.store.list_records("progress", owner, doc_id)}
        nodes = {node_id: {"state": records.get(node_id, {}).get("state", "not_learned"),
                           "source": records.get(node_id, {}).get("source"),
                           "updated_at": records.get(node_id, {}).get("updated_at")}
                 for node_id in self.graph.learnable_nodes}
        modules = [{"module_id": module_id,
                    "learned": sum(nodes.get(n, {}).get("state") == "learned" for n in module.get("node_ids", [])),
                    "total": len(module.get("node_ids", []))}
                   for module_id, module in self.graph.modules.items()]
        return {"contract_version": "progress-1", "doc_id": doc_id, "nodes": nodes, "modules": modules}
