from threading import RLock
from types import SimpleNamespace

from wayfinder.api.errors import WebError


class LearningGateway:
    def __init__(self, courses, runtime, graph_loader, *, media=None):
        self.courses, self.runtime, self.graph_loader = courses, runtime, graph_loader
        from wayfinder.infrastructure.document_requests import DocumentRequests
        runtime.document_requests = DocumentRequests(courses.store.engine, courses.settings, runtime.clock)
        self.media = media
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

    def lecture_context(self, actor, cid, node_id):
        course, graph = self._context(actor, cid)
        if node_id not in graph.learnable_nodes:
            raise WebError('not_found', 'Không tìm thấy nội dung yêu cầu')
        return course, graph

    def get_lecture(self, actor, cid, node_id):
        from wayfinder.application.lecture_view import public_lecture
        course, graph = self.lecture_context(actor, cid, node_id)
        raw = self.runtime.lecture(graph).make(course.doc_id, course.published_graph_version,
            graph, node_id, owner=actor.user_id, cache_only=True)
        progress = self.runtime.progress(graph).get_progress(actor.user_id, course.doc_id)['nodes']
        return public_lecture(raw, course, graph, progress, self.media)

    def stream_lecture(self, actor, cid, node_id, on_event):
        from wayfinder.application.lecture_view import public_lecture
        course, graph = self.lecture_context(actor, cid, node_id)

        def emit(event):
            kind = event.get('event')
            if kind == 'delta':
                on_event({'event': 'delta', 'text': event['text']})
            elif kind in {'skeleton', 'final', 'failure'}:
                progress = self.runtime.progress(graph).get_progress(actor.user_id, course.doc_id)['nodes']
                on_event({'event': kind, 'lecture': public_lecture(event['lecture'], course, graph, progress, self.media)})

        return self.runtime.lecture(graph).make(course.doc_id, course.published_graph_version,
            graph, node_id, owner=actor.user_id, allow_spend=True, on_event=emit)

    def open_source_page(self, actor, cid, page):
        course, graph = self._context(actor, cid)
        if not self.media:
            raise WebError('not_found', 'Tài liệu không có trang để xem')
        return self.media.open_source_page(course, graph, page)

    def open_source_file(self, actor, cid):
        course, graph = self._context(actor, cid)
        if not self.media:
            raise WebError('not_found', 'Không có tệp tài liệu')
        return self.media.open_source_file(course, graph)

    def get_media(self, actor, cid, asset_key):
        course, graph = self._context(actor, cid)
        if not self.media:
            raise WebError('not_found', 'Không tìm thấy nội dung yêu cầu')
        return self.media.get_media(course, graph, asset_key)

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

    def _owned_session(self, actor, cid, sid):
        course, graph = self._context(actor, cid)
        session = self.runtime.sessions(graph).get(actor.user_id, sid)
        if session is None or session['doc_id'] != course.doc_id:
            raise WebError('not_found', 'Không tìm thấy phiên học')
        return course, graph, session

    def list_sessions(self, actor, cid, filter='roadmap_page'):
        from wayfinder.application.assistant_view import session_view
        course, graph = self._context(actor, cid)
        if filter not in {'all', 'roadmap_page'} and not (filter.startswith('module:') and filter[7:] in graph.modules):
            raise WebError('validation', 'Bộ lọc phiên không hợp lệ')
        return {'course_id': cid, 'source_document': self.media.describe_source(course, graph) if self.media else None,
            'sessions': [session_view(row) for row in
            self.runtime.sessions(graph).list_sessions(actor.user_id, course.doc_id, filter)]}

    def create_session(self, actor, cid, scope):
        from wayfinder.application.assistant_view import session_view
        course, graph = self._context(actor, cid)
        if scope.get('kind') == 'roadmap':
            saved = {'kind': 'roadmap'}
        elif scope.get('kind') == 'module' and scope.get('module_id') in graph.modules:
            mid = scope['module_id']
            saved = {'kind': 'module', 'module_id_at_creation': mid,
                'graph_version_at_creation': course.published_graph_version,
                'node_ids': [nid for nid in graph.modules[mid]['node_ids'] if nid in graph.learnable_nodes]}
            if not saved['node_ids']:
                raise WebError('validation', 'Module chưa có bài học')
        else:
            raise WebError('validation', 'Phạm vi phiên không hợp lệ')
        with self.runtime.store.atomic():
            row = self.runtime.sessions(graph).create_session(actor.user_id, course.doc_id, saved)
        return session_view(row)

    def rename_session(self, actor, cid, sid, title):
        from wayfinder.application.assistant_view import session_view
        from wayfinder.infrastructure.assistant_requests import AssistantRequests
        def update():
            _, graph, _ = self._owned_session(actor, cid, sid)
            with self.runtime.store.atomic():
                return session_view(self.runtime.sessions(graph).rename_session(actor.user_id, sid, title))
        self._owned_session(actor, cid, sid)
        with AssistantRequests(self.courses.store.engine, self.courses.settings, self.runtime.clock).serial(sid):
            return update()

    def delete_session(self, actor, cid, sid):
        from wayfinder.infrastructure.assistant_requests import AssistantRequests
        def remove():
            _, graph, _ = self._owned_session(actor, cid, sid)
            with self.runtime.store.atomic():
                return self.runtime.sessions(graph).delete_session(actor.user_id, sid)
        self._owned_session(actor, cid, sid)
        with AssistantRequests(self.courses.store.engine, self.courses.settings, self.runtime.clock).serial(sid):
            return remove()

    def _artifact(self, actor, course, graph, item):
        kind, aid = item.get('kind'), item.get('id')
        if kind == 'lecture' and item.get('node_id') in graph.learnable_nodes:
            nid = item['node_id']
            return {'kind': 'lecture', 'id': str(aid or ''), 'node_id': nid, 'module_id': graph.nodes[nid]['module_id'],
                'title': graph.nodes[nid].get('display_name') or graph.nodes[nid].get('name', 'Bài học')}
        record = self.runtime.store.get_record({'quiz': 'quiz_attempt', 'document': 'documents'}.get(kind, ''), aid or '')
        if not record or record.get('owner') != actor.user_id or record.get('doc_id') != course.doc_id:
            return None
        if record.get('status') != 'ready':
            return None
        return {'kind': kind, 'id': aid, 'title': record.get('title') or ('Quiz ôn tập' if kind == 'quiz' else 'Tài liệu học tập')}

    def _answer_view(self, actor, course, graph, raw, focus=None):
        from wayfinder.application.assistant_view import answer_view
        artifacts = [result for item in raw.get('artifacts', []) if (result := self._artifact(actor, course, graph, item))]
        result = answer_view(raw, course, graph, artifacts)
        # Core decides focus validity. The web reflects a null result without dropping/changing the submitted ID.
        result['warnings'] = ['focus_ignored'] if focus is not None and raw.get('focus_node_id') is None else []
        if any(call.get('name') == 'make_document' and call.get('result_summary', {}).get('error', {}).get('code') == 'rate_limited'
               for call in raw.get('tool_calls', [])):
            result['warnings'].append('document_rate_limited')
        return result

    def list_turns(self, actor, cid, sid):
        from doc2roadmap.domain.phase_b_limits import context_hash
        course, graph, _ = self._owned_session(actor, cid, sid)
        turns = []
        for row in self.runtime.sessions(graph).list_turns(actor.user_id, sid):
            key = context_hash([actor.user_id, course.doc_id, sid, row.get('client_turn_id')])
            intent = self.runtime.store.get_record('web_assistant_intent', key) or {}
            turns.append({key: row.get(key) for key in ('contract_version', 'turn_id', 'client_turn_id', 'question', 'created_at')}
                | {'answer': self._answer_view(actor, course, graph, row['answer'], intent.get('payload', {}).get('focus_node_id'))})
        return {'course_id': cid, 'session_id': sid, 'turns': turns}

    def prepare_turn(self, actor, cid, sid, key, question, focus=None):
        from wayfinder.infrastructure.assistant_requests import AssistantRequests
        course, _, _ = self._owned_session(actor, cid, sid)
        AssistantRequests(self.courses.store.engine, self.courses.settings, self.runtime.clock).admit(
            actor, course, sid, key, question, focus)

    def ask_stream(self, actor, cid, sid, key, question, on_event, focus=None):
        from wayfinder.application.assistant_view import TOOL_LABELS, cards_view
        from wayfinder.infrastructure.assistant_requests import AssistantRequests
        def generate():
            course, graph, _ = self._owned_session(actor, cid, sid)
            for previous in self.runtime.sessions(graph).list_turns(actor.user_id, sid):
                if previous.get('client_turn_id') == key:
                    on_event({'event': 'final', 'answer': self._answer_view(actor, course, graph, previous['answer'], focus)})
                    return previous['answer']
            def emit(row):
                kind = row.get('event')
                if kind == 'delta':
                    on_event({'event': 'delta', 'text': row['text']})
                elif kind == 'progress':
                    on_event({'event': 'progress', 'text': 'Đang chuẩn bị câu trả lời…'})
                elif kind == 'tool_call':
                    on_event({'event': 'tool_call', 'name': row.get('name') if row.get('name') in TOOL_LABELS else 'other',
                        'text': TOOL_LABELS.get(row.get('name'), 'Đang xử lý yêu cầu…')})
                elif kind == 'graph_card':
                    on_event({'event': kind, 'graph_cards': cards_view(row, graph)})
                elif kind == 'artifact':
                    artifact = self._artifact(actor, course, graph, row)
                    if artifact:
                        on_event({'event': kind, 'artifact': artifact})
                elif kind in {'final', 'failure'}:
                    on_event({'event': kind, 'answer': self._answer_view(actor, course, graph, row['answer'], focus)})
            def tool_started(name):
                on_event({'event': 'tool_call', 'name': name if name in TOOL_LABELS else 'other',
                    'text': TOOL_LABELS.get(name, 'Đang xử lý yêu cầu…'), 'state': 'running'})
            return self.runtime.assistant(graph, on_tool_start=tool_started).ask(course.doc_id, course.published_graph_version, sid, question,
                owner=actor.user_id, client_turn_id=key, focus_node_id=focus, allow_spend=True, on_event=emit)
        self._owned_session(actor, cid, sid)
        with AssistantRequests(self.courses.store.engine, self.courses.settings, self.runtime.clock).serial(sid):
            return generate()

    def get_assistant_artifact(self, actor, cid, sid, kind, aid):
        from wayfinder.application.lecture_view import pick
        course, graph, session = self._owned_session(actor, cid, sid)
        if {'kind': kind, 'artifact_id': aid} not in session.get('artifact_refs', []):
            raise WebError('not_found', 'Không tìm thấy nội dung')
        verified = self._artifact(actor, course, graph, {'kind': kind, 'id': aid})
        if verified is None:
            raise WebError('not_found', 'Không tìm thấy nội dung')
        if kind == 'document':
            raw = self.runtime.document(graph).get(aid, owner=actor.user_id)
            return {**verified, **pick(raw, ('contract_version', 'markdown', 'sources'))}
        if kind == 'quiz':
            raw = self.runtime.quiz(graph).get_attempt(aid, actor.user_id)
            return {**verified, 'contract_version': raw['contract_version'], 'items': [
                {'item_id': row['item_id'], 'question': row.get('question') or row.get('stem', ''),
                 'options': [pick(option, ('option_id', 'text')) for option in row.get('options', [])]}
                for row in raw['items']]}
        raise WebError('not_found', 'Không tìm thấy nội dung')

    def list_library(self, actor, cid, scope='all'):
        from doc2roadmap.application.phase_b.library import LibraryUseCase
        course, graph = self._context(actor, cid)
        if scope not in {'all', 'roadmap'} and not (scope.startswith('module:') and scope[7:] in graph.modules):
            raise WebError('validation', 'Bộ lọc thư viện không hợp lệ')
        return {'course_id': cid, **LibraryUseCase(self.runtime.store, graph, settings=self.runtime.settings,
            clock=self.runtime.clock).list_library(actor.user_id, course.doc_id, scope)}

    @staticmethod
    def _content_scope(graph, module_id=None):
        if module_id is None:
            return {'kind': 'roadmap'}
        if module_id not in graph.modules:
            raise WebError('not_found', 'Không tìm thấy module')
        return {'kind': 'module', 'module_id_at_creation': module_id,
            'graph_version_at_creation': graph.graph_version,
            'node_ids': [nid for nid in graph.modules[module_id]['node_ids'] if nid in graph.learnable_nodes]}

    def prepare_quiz(self, actor, cid, scope):
        course, graph = self._context(actor, cid)
        if scope.get('kind') == 'module' and not scope.get('module_id'):
            raise WebError('validation', 'Hãy chọn module để làm quiz')
        home = self._content_scope(graph, scope.get('module_id') if scope.get('kind') == 'module' else None)
        return course, graph, home

    def make_quiz(self, actor, cid, scope, n=None, on_event=None):
        from wayfinder.application.content_view import quiz_item, quiz_view
        course, graph, home = self.prepare_quiz(actor, cid, scope)
        def emit(row):
            if on_event and row.get('event') == 'item_ready':
                on_event({'event': 'item_ready', 'attempt_id': row['attempt_id'], 'item': quiz_item(row['item'])})
        raw = self.runtime.quiz(graph).make_quiz(course.doc_id, owner=actor.user_id, scope=home,
            graph_version=course.published_graph_version, origin='button', home_scope=home, allow_spend=True,
            n=n, on_event=emit)
        result = quiz_view(raw, course, self.media.describe_source(course, graph) if self.media else None)
        if on_event:
            on_event({'event': 'final', 'quiz': result})
        return result

    def _owned_content(self, actor, cid, kind, aid):
        course, graph = self._context(actor, cid)
        row = self.runtime.store.get_record(kind, aid)
        if not row or row.get('owner') != actor.user_id or row.get('doc_id') != course.doc_id:
            raise WebError('not_found', 'Không tìm thấy nội dung yêu cầu')
        return course, graph, row

    def get_quiz(self, actor, cid, aid):
        from wayfinder.application.content_view import quiz_view
        course, graph, stored = self._owned_content(actor, cid, 'quiz_attempt', aid)
        raw = self.runtime.quiz(graph).get_attempt(aid, actor.user_id)
        return quiz_view({**raw, 'submission': bool(stored.get('submission'))}, course, self.media.describe_source(course, graph) if self.media else None)

    def get_quiz_result(self, actor, cid, aid):
        from wayfinder.application.content_view import result_view
        _, _, row = self._owned_content(actor, cid, 'quiz_attempt', aid)
        if not row.get('submission'):
            raise WebError('not_found', 'Quiz này chưa được nộp')
        return result_view({**row['submission'], 'contract_version': row['contract_version'], 'attempt_id': aid})

    def submit_quiz(self, actor, cid, aid, answers):
        from wayfinder.application.content_view import result_view
        # Core submission and progress writes share this short PostgreSQL transaction.
        with self.runtime.store.atomic():
            _, graph, row = self._owned_content(actor, cid, 'quiz_attempt', aid)
            if row.get('status') != 'ready':
                raise WebError('conflict', 'Quiz chưa sẵn sàng để nộp')
            allowed = {item['item_id']: {option['option_id'] for option in item['options']} for item in row['items']}
            if any(key not in allowed or value not in allowed[key] for key, value in answers.items()):
                raise WebError('validation', 'Lựa chọn không thuộc đề quiz này')
            if row.get('submission'):
                if row['submission']['answers'] != answers:
                    raise WebError('conflict', 'Quiz đã được nộp. Hãy mở một lần làm mới.')
                return self.get_quiz_result(actor, cid, aid)
            return result_view(self.runtime.quiz(graph).submit(aid, actor.user_id, answers))

    def prepare_document(self, actor, cid, module_ids, home_module_id=None):
        course, graph = self._context(actor, cid)
        modules = list(dict.fromkeys(module_ids))
        if not modules or any(mid not in graph.modules for mid in modules):
            raise WebError('validation', 'Hãy chọn module thuộc lộ trình này')
        if len(modules) > self.runtime.settings.document_max_modules:
            raise WebError('scope_too_large', 'Chọn tối đa 5 module hoặc thu hẹp phạm vi để tạo tài liệu.')
        return course, graph, modules, self._content_scope(graph, home_module_id)

    def admit_document(self, actor):
        self.runtime.document_requests.admit(actor.user_id)

    def make_document(self, actor, cid, request, module_ids, home_module_id=None, on_event=None):
        from wayfinder.application.content_view import document_view
        course, graph, modules, home = self.prepare_document(actor, cid, module_ids, home_module_id)
        source = self.media.describe_source(course, graph) if self.media else None
        def emit(row):
            if not on_event:
                return
            kind = row['event']
            if kind in {'skeleton', 'delta'}:
                on_event({key: row[key] for key in ('event', 'document_id', 'title', 'text') if key in row})
            elif kind in {'final', 'failure'}:
                on_event({'event': kind, 'document': document_view(row['document'], course, source)})
        raw = self.runtime.document(graph).create(course.doc_id, course.published_graph_version, graph, request,
            {'module_ids': modules}, owner=actor.user_id, origin='button', home_scope=home,
            allow_spend=True, on_event=emit)
        return document_view(raw, course, source)

    def get_document(self, actor, cid, did):
        from wayfinder.application.content_view import document_view
        course, graph, _ = self._owned_content(actor, cid, 'documents', did)
        return document_view(self.runtime.document(graph).get(did, owner=actor.user_id), course,
            self.media.describe_source(course, graph) if self.media else None)

    def export_document(self, actor, cid, did):
        _, graph, _ = self._owned_content(actor, cid, 'documents', did)
        return self.runtime.document(graph).export(did, owner=actor.user_id)
