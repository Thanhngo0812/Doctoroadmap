"""Learner-owned sessions and complete assistant turn history."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from doc2roadmap.domain.phase_b_limits import BSettings, context_hash


def _now(clock):
    value = clock.now() if clock is not None else datetime.now(timezone.utc)
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError("clock.now() must return a timezone-aware datetime")
    return value.isoformat()


class SessionUseCase:
    def __init__(self, store, graph, settings: BSettings | None = None, clock=None):
        self.store, self.graph = store, graph
        self.settings = settings or BSettings()
        self.clock = clock

    def create_session(self, owner, doc_id, scope):
        if not owner or not doc_id or not isinstance(scope, dict):
            raise ValueError("owner, doc_id, and scope are required")
        if self.graph.doc_id and doc_id != self.graph.doc_id:
            raise ValueError("doc_id does not match graph")
        kind = scope.get("kind")
        if kind == "roadmap":
            saved_scope = {"kind": "roadmap"}
        elif kind == "module":
            node_ids = list(dict.fromkeys(str(item) for item in scope.get("node_ids", [])))
            if not node_ids or any(node_id not in self.graph.nodes for node_id in node_ids):
                raise ValueError("module scope must contain known node_ids")
            saved_scope = {"kind": "module", "node_ids": node_ids,
                           "module_id_at_creation": scope.get("module_id_at_creation"),
                           "graph_version_at_creation": scope.get("graph_version_at_creation",
                                                                   getattr(self.graph, "graph_version", None))}
        else:
            raise ValueError("scope.kind must be roadmap or module")
        now = _now(self.clock)
        session_id = uuid4().hex
        row = {"contract_version": "session-1", "session_id": session_id,
               "owner": owner, "doc_id": doc_id, "scope": saved_scope,
               "title": "Phiên học mới", "title_source": "rule",
               "created_at": now, "updated_at": now, "turn_count": 0,
               "last_question_preview": "", "artifact_refs": [],
               "state": {"reminded_node_ids": [], "linked_node_ids": [], "reminders_enabled": True}}
        self.store.put_record("session", session_id, row)
        return row

    def get(self, owner, session_id):
        row = self.store.get_record("session", session_id)
        return row if row and row.get("owner") == owner and (
            not self.graph.doc_id or row.get("doc_id") == self.graph.doc_id) else None

    def list_sessions(self, owner, doc_id, filter="all"):
        if self.graph.doc_id and doc_id != self.graph.doc_id:
            raise ValueError("doc_id does not match graph")
        rows = [row for row in self.store.list_records("session", owner=owner)
                if row.get("doc_id") == doc_id]
        annotated = [self._annotate(row) for row in rows]
        if filter == "all":
            selected = annotated
        elif filter == "roadmap_page":
            roadmaps = [row for row in annotated if row["scope"].get("kind") == "roadmap" or row.get("scope_note")]
            modules = [row for row in annotated if row["scope"].get("kind") == "module" and not row.get("scope_note")]
            modules.sort(key=lambda row: (row.get("updated_at", ""), row.get("session_id", "")), reverse=True)
            selected = roadmaps + modules[:self._setting("roadmap_recent_module_sessions", 5)]
        elif isinstance(filter, str) and filter.startswith("module:"):
            module_id = filter.partition(":")[2]
            selected = [row for row in annotated if not row.get("scope_note")
                        and row.get("resolved_module_id") == module_id]
        else:
            raise ValueError("filter must be all, roadmap_page, or module:<module_id>")
        return sorted(selected, key=lambda row: (row.get("updated_at", ""), row.get("session_id", "")), reverse=True)

    def rename_session(self, owner, session_id, title):
        row = self._owned(owner, session_id)
        if not isinstance(title, str) or not title.strip():
            raise ValueError("title must not be empty")
        row["title"] = title.strip()[:self._setting("session_title_max_chars", 60)]
        row["title_source"] = "learner"
        row["updated_at"] = _now(self.clock)
        self.store.put_record("session", session_id, row)
        return row

    def delete_session(self, owner, session_id):
        row = self._owned(owner, session_id)
        self.store.delete_record("session", session_id)
        for turn in self.store.list_records("turn", owner=owner):
            if turn.get("session_id") == session_id:
                self.store.delete_record("turn", turn["turn_id"])
        return {"deleted": True, "session_id": row["session_id"]}

    def list_turns(self, owner, session_id):
        session = self.store.get_record("session", session_id)
        if session and (session.get("owner") != owner or
                        self.graph.doc_id and session.get("doc_id") != self.graph.doc_id):
            raise KeyError(session_id)
        if session is None:
            return []
        rows = [row for row in self.store.list_records("turn", owner=owner)
                if row.get("session_id") == session_id]
        return sorted(rows, key=lambda row: (row.get("created_at", ""), row.get("turn_id", "")))

    def append_turn(self, owner, session_id, question, answer, *, client_turn_id=None,
                    linked_node_ids=None, artifact_refs=None, state=None):
        session = self._owned(owner, session_id)
        if (not isinstance(question, str) or not question.strip() or not isinstance(answer, dict)
                or answer.get("contract_version") not in {"answer-2", "answer-3"}):
            raise ValueError("a question and answer-2 or answer-3 object are required")
        if client_turn_id:
            key = context_hash([session_id, client_turn_id])
            existing = self.store.get_record("turn", key)
            if existing:
                return existing
            turn_id = key
        else:
            turn_id = uuid4().hex
        now = _now(self.clock)
        turn = {"contract_version": "turn-1", "turn_id": turn_id,
                "session_id": session_id, "client_turn_id": client_turn_id,
                "question": question, "answer": answer, "created_at": now,
                "owner": owner, "doc_id": session["doc_id"]}
        self.store.put_record("turn", turn_id, turn)
        session["turn_count"] = len(self.list_turns(owner, session_id))
        session["last_question_preview"] = self._preview(question)
        session["updated_at"] = now
        if session["title_source"] == "rule" and session["turn_count"] == 1:
            nodes = linked_node_ids or answer.get("linked_node_ids", [])
            if nodes and nodes[0] in self.graph.nodes:
                node = self.graph.nodes[nodes[0]]
                title = node.get("display_name") or node.get("name") or node.get("raw_name")
            else:
                title = question.strip()
            session["title"] = self._preview(title, self._setting("session_title_max_chars", 60))
        if state is not None:
            session["state"] = state
        if artifact_refs:
            refs = session.setdefault("artifact_refs", [])
            for ref in artifact_refs:
                if ref not in refs:
                    refs.append(ref)
        self.store.put_record("session", session_id, session)
        return turn

    def add_artifact_ref(self, owner, session_id, kind, artifact_id):
        session = self._owned(owner, session_id)
        ref = {"kind": kind, "artifact_id": artifact_id}
        refs = session.setdefault("artifact_refs", [])
        if ref not in refs:
            refs.append(ref)
            session["updated_at"] = _now(self.clock)
            self.store.put_record("session", session_id, session)
        return ref

    def _owned(self, owner, session_id):
        row = self.get(owner, session_id)
        if row is None:
            raise KeyError(session_id)
        return row

    def _annotate(self, row):
        result = dict(row)
        scope = row.get("scope", {})
        result["resolved_module_id"] = None
        if scope.get("kind") == "module":
            from doc2roadmap.domain.scope import resolve_scope
            resolved = resolve_scope(scope, self.graph,
                                     min_jaccard=self._setting("scope_remap_min_jaccard", 0.5))
            result["resolved_module_id"] = resolved["module_id"]
            if resolved["stale"]:
                result["scope_note"] = "module này đã đổi"
            elif resolved["module_id"]:
                result["module_label"] = self.graph.modules[resolved["module_id"]].get("title")
        return result

    def _preview(self, text, limit=80):
        text = " ".join(str(text).split())
        max_chars = max(1, int(limit))
        if len(text) <= max_chars:
            return text
        return text[:max_chars].rsplit(" ", 1)[0].rstrip() or text[:max_chars]

    def _setting(self, name, default):
        return self.settings.get(name, default) if isinstance(self.settings, dict) else getattr(self.settings, name, default)
