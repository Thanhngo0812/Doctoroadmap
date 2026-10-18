"""Scope-aware listing for saved document and quiz artifacts."""
from __future__ import annotations

from doc2roadmap.domain.phase_b_limits import BSettings


class LibraryUseCase:
    def __init__(self, store, graph, settings: BSettings | None = None, clock=None):
        self.store, self.graph = store, graph
        self.settings, self.clock = settings or BSettings(), clock

    def list_library(self, owner, doc_id, scope_filter="all"):
        if not owner or not doc_id:
            raise ValueError("owner and doc_id are required")
        if self.graph.doc_id and doc_id != self.graph.doc_id:
            raise ValueError("doc_id does not match graph")
        filter_kind, module_id = self._filter(scope_filter)
        records = []
        for kind, record_kind in (("document", "documents"), ("quiz_attempt", "quiz_attempt")):
            for row in self.store.list_records(record_kind, owner=owner):
                if row.get("doc_id") != doc_id:
                    continue
                item = self._item(kind, row, filter_kind, module_id)
                if item is not None:
                    records.append(item)
        records.sort(key=lambda row: (row.get("created_at", ""), row["id"]), reverse=True)
        return {"contract_version": "library-1", "doc_id": doc_id,
                "scope_filter": scope_filter, "items": records}

    def _item(self, kind, record, filter_kind, selected_module):
        home = record.get("home_scope")
        node_ids = set(record.get("node_ids", []))
        if filter_kind == "all":
            group = "here"
        elif filter_kind == "roadmap":
            if not isinstance(home, dict) or home.get("kind") != "roadmap":
                return None
            group = "here"
        else:
            resolved_home = self._resolve(home)
            if resolved_home == selected_module:
                group = "here"
            else:
                current_nodes = set(self.graph.modules.get(selected_module, {}).get("node_ids", []))
                if not current_nodes.intersection(node_ids):
                    return None
                group = "elsewhere"
        module_ids = {self.graph.nodes[node_id].get("module_id")
                      for node_id in node_ids if node_id in self.graph.nodes}
        labels = [self.graph.modules[mid].get("title") or mid for mid in sorted(
            module_ids, key=lambda mid: self.graph.modules.get(mid, {}).get("index", 10**9))
            if mid in self.graph.modules]
        item = {"kind": kind, "id": record.get("document_id") or record.get("attempt_id"),
                "title": record.get("title") or record.get("request") or
                         ("Quiz" if kind == "quiz_attempt" else "Tài liệu học tập"),
                "created_at": record.get("created_at"), "origin": record.get("origin"),
                "group": group, "module_labels": labels}
        if kind == "quiz_attempt" and ("score" in record or "submission" in record):
            score = record.get("score")
            submission = record.get("submission") or {}
            if score is None and "correct_count" in submission and "question_count" in submission:
                score = {"correct": submission["correct_count"], "total": submission["question_count"]}
            item["score"] = score
        if group == "elsewhere":
            item["label"] = "tạo ở nơi khác"
        if record.get("session_id"):
            session = self.store.get_record("session", record["session_id"])
            if session is None:
                item["session_deleted"] = True
        return item

    def _resolve(self, scope):
        if not isinstance(scope, dict) or scope.get("kind") != "module":
            return None
        from doc2roadmap.domain.scope import resolve_scope
        result = resolve_scope(scope, self.graph,
                               min_jaccard=self._setting("scope_remap_min_jaccard", 0.5))
        return None if result["stale"] else result["module_id"]

    @staticmethod
    def _filter(scope_filter):
        if isinstance(scope_filter, dict):
            kind = scope_filter.get("kind")
            module_id = scope_filter.get("module_id")
            if kind == "module" and module_id:
                return kind, module_id
            if kind == "roadmap":
                return kind, None
        elif scope_filter == "all":
            return "all", None
        elif scope_filter == "roadmap":
            return "roadmap", None
        elif isinstance(scope_filter, str) and scope_filter.startswith("module:"):
            return "module", scope_filter.partition(":")[2]
        raise ValueError("scope_filter must be all, roadmap, or module:<module_id>")

    def _setting(self, name, default):
        return self.settings.get(name, default) if isinstance(self.settings, dict) else getattr(self.settings, name, default)
