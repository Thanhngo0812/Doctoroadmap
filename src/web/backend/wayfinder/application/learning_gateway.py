from threading import RLock
from types import SimpleNamespace

from wayfinder.api.errors import WebError


class LearningGateway:
    def __init__(self, courses, runtime, graph_loader):
        self.courses, self.runtime, self.graph_loader = courses, runtime, graph_loader
        self._graphs = {}
        self._graph_lock = RLock()

    def _context(self, actor, cid):
        course, _ = self.courses.require_course(actor, cid, action="learn")
        if course.status != "ready" or course.published_graph_version is None:
            raise WebError("conflict", "Khoá học chưa sẵn sàng")
        key = course.doc_id, course.published_graph_version
        with self._graph_lock:
            if key not in self._graphs:
                graph = self.graph_loader(*key)
                if (graph.doc_id, graph.graph_version) != key:
                    raise ValueError("learning graph does not match published course version")
                self._graphs[key] = graph
            graph = self._graphs[key]
        self.courses.store.touch(cid, actor.user_id, self.runtime.clock.now())
        return course, graph

    def learner(self, actor, cid, **_untrusted):
        """Server-bound context for learning endpoints; request owner/doc/version are ignored."""
        course, graph = self._context(actor, cid)
        return SimpleNamespace(owner=actor.user_id, doc_id=course.doc_id,
            graph_version=course.published_graph_version, graph=graph,
            sessions=self.runtime.sessions(graph), progress=self.runtime.progress(graph),
            spend_guard=self.runtime.spend_guard)

    def sample_blueprint(self, actor, doc_id):
        from wayfinder.application.seed_samples import SAMPLE_DOCS
        self.courses.authorize(actor, "seed_samples")
        if self.courses.settings.env != "dev" or doc_id not in SAMPLE_DOCS:
            raise WebError("not_found", "Không tìm thấy nội dung yêu cầu")
        graph = self.graph_loader(doc_id, None)
        if graph.doc_id != doc_id or not graph.modules or not isinstance(graph.graph_version, int):
            raise WebError("conflict", "Chưa có lộ trình hoàn tất")
        with self._graph_lock:
            self._graphs[(doc_id, graph.graph_version)] = graph
        return {"graph_version": graph.graph_version, "module_count": len(graph.modules)}

    def get_roadmap(self, actor, cid):
        course, graph = self._context(actor, cid)
        progress = self.runtime.progress(graph).get_progress(actor.user_id, course.doc_id)
        modules_progress = self._module_progress(graph, progress["nodes"])
        module_progress = {row["module_id"]: {"learned": row["learned"], "total": row["total"]}
                           for row in modules_progress}
        modules = []
        for module in sorted(graph.modules.values(), key=lambda row: row.get("index", 0)):
            modules.append({"module_id": module["module_id"], "index": module.get("index", 0),
                "title": module.get("display_name") or module.get("title") or "",
                "description": module.get("description") or "",
                "concepts": [{"node_id": nid, "name": graph.nodes[nid].get("display_name") or graph.nodes[nid].get("name", "")}
                             for nid in module.get("node_ids", []) if nid in graph.learnable_nodes],
                "progress": module_progress.get(module["module_id"], {"learned": 0, "total": 0})})
        return {"course_id": cid, "doc_id": course.doc_id, "graph_version": course.published_graph_version,
                "progress": {"learned": sum(node["state"] == "learned" for node in progress["nodes"].values()),
                             "total": len(progress["nodes"])},
                "modules": modules}

    def get_progress(self, actor, cid):
        course, graph = self._context(actor, cid)
        result = self.runtime.progress(graph).get_progress(actor.user_id, course.doc_id)
        result["modules"] = self._module_progress(graph, result["nodes"])
        return {"course_id": cid, **result}

    def set_progress(self, actor, cid, node_id, learned):
        course, graph = self._context(actor, cid)
        if node_id not in graph.learnable_nodes:
            raise WebError("not_found", "Không tìm thấy nội dung yêu cầu")
        try:
            self.runtime.progress(graph).set_progress(actor.user_id, course.doc_id, node_id, learned)
        except ValueError as exc:
            if str(exc) == "learned must be boolean":
                raise WebError("validation", "Trạng thái tiến độ không hợp lệ") from None
            raise
        return self.get_progress(actor, cid)

    @staticmethod
    def _module_progress(graph, nodes):
        summaries = []
        for module_id, module in graph.modules.items():
            node_ids = set(module.get("node_ids", ())) & nodes.keys()
            summaries.append({"module_id": module_id,
                "learned": sum(nodes[node_id]["state"] == "learned" for node_id in node_ids),
                "total": len(node_ids)})
        return summaries

    def course_summary(self, actor, cid):
        course, graph = self._context(actor, cid)
        progress = self.runtime.progress(graph).get_progress(actor.user_id, course.doc_id)
        sessions = self.runtime.sessions(graph).list_sessions(actor.user_id, course.doc_id)
        ordered = sorted(graph.modules.values(), key=lambda row: row.get("index", 0))
        resume = None
        for session in sorted(sessions, key=lambda row: row.get("updated_at", ""), reverse=True):
            scope = session.get("scope", {})
            module_id = session.get("resolved_module_id")
            if scope.get("kind") == "module" and module_id in graph.modules:
                resume = module_id
                break
        if resume is None:
            recent = sorted(progress["nodes"].items(), key=lambda item: item[1].get("updated_at") or "", reverse=True)
            for nid, row in recent:
                if row.get("updated_at"):
                    resume = next((m["module_id"] for m in ordered if nid in m.get("node_ids", [])), None)
                    if resume:
                        break
        if resume is None and ordered:
            resume = ordered[0]["module_id"]
        return {"progress": {"learned": sum(row["state"] == "learned" for row in progress["nodes"].values()),
                             "total": len(progress["nodes"])}, "resume": {"module_id": resume} if resume else None}
