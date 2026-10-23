"""Tutor-style document assistant (`answer-3`): context fetched first, tools only when needed, checks only logged."""
from __future__ import annotations

import json
import logging
import re
from copy import deepcopy
from time import perf_counter
from uuid import uuid4

from doc2roadmap.application.phase_b.common import stable_json
from doc2roadmap.application.phase_b.budget import DailyLimitExceeded, DailySpendGuard, spending_call
from doc2roadmap.application.phase_b import assistant_context as ctx
from doc2roadmap.application.phase_b.lecture_context3 import formula_pages
from doc2roadmap.application.phase_b.lectures import LectureUseCase
from doc2roadmap.application.phase_b.progress import ProgressUseCase
from doc2roadmap.application.phase_b.sessions import SessionUseCase
from doc2roadmap.application.phase_b.clock import SystemClock
from doc2roadmap.application.ports.phase_b import Delta, Done, ToolCall
from doc2roadmap.domain.learning_graph import LearningGraph
from doc2roadmap.domain.phase_b_limits import BSettings, context_hash, usage_row
from doc2roadmap.domain.phase_b_pricing import estimate_cost, token_cost
from doc2roadmap.domain.retrieval import HybridRetriever, RetrievalDocument
from doc2roadmap.domain.scope import resolve_scope


REF = re.compile(r'\[((?:CT|S|N|Q|R|H|B|K|D)\d+)\]')
IDEA_REF = re.compile(r'\s*' + REF.pattern)
# Not used by the assistant any more; scripts/phase-b/sa55_assistant_run.py (answer-2 evaluation) still imports it until SA-23.
REFUSAL = 'Tài liệu hiện có chưa cung cấp đủ bằng chứng để trả lời câu hỏi này.'
IMAGE_TOKEN_ESTIMATE = 1300
DAILY_LIMIT_TEXT = 'Đã hết hạn mức chi hôm nay. Bạn vẫn có thể dùng bài giảng và nội dung đã có.'
ARTIFACT_TEXT = 'Đã tạo nội dung theo yêu cầu. Bạn có thể mở bằng liên kết đính kèm.'
FAILURES = {
    'loi_mang': 'Chưa kết nối được tới mô hình để trả lời. Bạn thử lại sau ít phút.',
    'khong_dung_duoc': 'Mô hình chưa viết được câu trả lời dùng được. Bạn thử lại.',
    'het_ngan_sach_cau': 'Câu hỏi này cần nhiều lượt xử lý hơn mức cho phép. Bạn thử hỏi gọn hơn hoặc thử lại.',
}
log = logging.getLogger(__name__)


def _value(item, key, default=None):
    return item.get(key, default) if isinstance(item, dict) else getattr(item, key, default)


def _declaration(name, description, properties, required):
    return {'name': name, 'description': description, 'parameters': {
        'type': 'object', 'properties': properties, 'required': required, 'additionalProperties': False}}


def _string():
    return {'type': 'string'}


SEARCH_SCOPES = ['uu_tien_module', 'ca_tai_lieu']

TOOLS = [
    _declaration('search_document', 'Tìm bằng chứng trong tài liệu. scope là uu_tien_module (mặc định, ưu tiên module '
                 'đang mở) hoặc ca_tai_lieu (cả tài liệu).',
                 {'query': _string(), 'scope': {'type': 'string', 'enum': SEARCH_SCOPES}, 'k': {'type': 'integer', 'minimum': 1, 'maximum': 6}}, ['query']),
    _declaration('lookup_concept', 'Tìm tên, alias hoặc mô tả khái niệm.', {'name': _string()}, ['name']),
    _declaration('why_here', 'Tiên quyết trực tiếp kèm bằng chứng.', {'concept': _string()}, ['concept']),
    _declaration('get_module_info', 'Thông tin module.', {'module': _string()}, ['module']),
    _declaration('path_to', 'Lộ trình tới khái niệm.', {'target': _string()}, ['target']),
    _declaration('traverse', 'Đi theo cạnh có bằng chứng.',
                 {'concept': _string(), 'edge_type': _string(), 'direction': {'type': 'string', 'enum': ['in', 'out']}},
                 ['concept', 'edge_type']),
    _declaration('get_media', 'Hình và bảng đã xác nhận.', {'concept': _string()}, ['concept']),
    _declaration('get_lecture', 'Mở bài giảng dùng chung với nút bấm.', {'concept': _string()}, ['concept']),
    _declaration('make_quiz', 'Tạo lần làm quiz, không trả đáp án.',
                 {'scope': {'type': ['string', 'array'], 'items': _string()},
                  'n': {'type': 'integer', 'minimum': 1, 'maximum': 10}, 'level': _string()}, ['scope']),
    _declaration('make_document', 'Tạo tài liệu có trích dẫn theo yêu cầu.',
                 {'request': _string(), 'scope': {'type': ['string', 'array'], 'items': _string()}}, ['request', 'scope']),
]


def _check_args(schema, args):
    if not isinstance(args, dict):
        return 'Tham số phải là object'
    if set(args) - set(schema['properties']) or set(schema['required']) - set(args):
        return 'Thiếu hoặc thừa tham số'
    for key, value in args.items():
        field = schema['properties'][key]
        types = field['type'] if isinstance(field['type'], list) else [field['type']]
        good = ('string' in types and isinstance(value, str) and bool(value.strip())
                or 'integer' in types and type(value) is int
                or 'array' in types and isinstance(value, list) and bool(value)
                   and all(isinstance(item, str) and item for item in value))
        if not good or ('enum' in field and value not in field['enum']):
            return f'Tham số {key} sai kiểu hoặc giá trị'
        if type(value) is int and not field.get('minimum', value) <= value <= field.get('maximum', value):
            return f'Tham số {key} vượt giới hạn'
    return None


class AssistantUseCase:
    def __init__(self, graph, store, model, *, search=None, concept_lookup=None,
                 lecture=None, quiz=None, document=None, settings=None, clock=None,
                 spend_guard=None, progress=None, page_images=None):
        self.graph, self.store, self.model = graph, store, model
        self.page_images = page_images
        self.search, self.concept_lookup = search, concept_lookup
        self.content_tools = {'get_lecture': lecture, 'make_quiz': quiz, 'make_document': document}
        self.settings = settings or BSettings()
        self.clock = clock or SystemClock()
        self.spend_guard = spend_guard or DailySpendGuard(store, settings=self.settings, clock=self.clock)
        self.progress = progress or ProgressUseCase(store, graph, clock=self.clock)
        self.sessions = SessionUseCase(store, graph, settings=self.settings, clock=self.clock)

    def _session_key(self, doc_id, session_id, owner):
        return context_hash([owner, doc_id, session_id])

    def session_state(self, doc_id, session_id, *, owner='local'):
        return self.store.get_record('assistant_state', self._session_key(doc_id, session_id, owner)) or {
            'owner': owner, 'doc_id': doc_id, 'session_id': session_id, 'turns': [],
            'reminded_node_ids': [], 'linked_node_ids': [], 'reminders_enabled': True}

    def _local_search(self, graph, question, current_module_id, k=4):
        retriever = HybridRetriever([RetrievalDocument(cid, _value(c, 'text', ''), (1.0,),
                                     doc_id=graph.doc_id or '', order_index=_value(c, 'order_index', 0))
                                     for cid, c in graph.chunks.items()])
        hits = retriever.search_bm25(question, top_k=20)
        return [{'chunk_id': hit.chunk_id, 'text': hit.document.text,
                 'page': _value(graph.chunks[hit.chunk_id], 'page'), 'score': hit.score}
                for hit in hits[:k]]

    def _scope_card(self, graph, scope, module_id, scope_note=None):
        if module_id is not None:
            return {"kind": "module", "module": graph.get_module_info(module_id, module_id),
                    "scope_note": scope_note}
        modules = [{"index": row.get("index", index) + 1,
                    "title": row.get("title") or row.get("name") or module_id,
                    "concept_count": len(row.get("node_ids", []))}
                   for index, (module_id, row) in enumerate(graph.modules.items())]
        return {"kind": "roadmap", "modules": modules, "scope_note": scope_note}

    def _prompt_scope_card(self, graph, scope, module_id, scope_note=None):
        card = self._scope_card(graph, scope, module_id, scope_note)
        if card["kind"] == "roadmap":
            card["modules"] = [[row["index"], row["title"], row["concept_count"]]
                               for row in card["modules"]]
        return card

    def _search(self, graph, query, module, *, scope='uu_tien_module', k=4):
        if self.search is None:
            return self._local_search(graph, query, module, k)
        result = self.search(query, scope=scope, k=k, current_module_id=module)
        if isinstance(result, dict):
            result = result.get('hits', result.get('documents', result.get('results', [])))
        return list(result)[:k]

    def _sources(self, graph, rows):
        result = []
        for row in rows:
            cid = _value(row, 'chunk_id')
            if cid not in graph.chunks:
                continue
            label = graph.sources.label(cid)
            # Context text is bounded, but citation resolution retains the original source.
            result.append({'label': label, 'chunk_id': cid, 'text': _value(row, 'text', _value(graph.chunks[cid], 'text', ''))[:1200],
                           'page': _value(graph.chunks[cid], 'page')})
        return result

    def _shown(self, graph, rows):
        """Passages shown to the model first: full text, section path, one row per chunk."""
        result = []
        for row in self._sources(graph, rows):
            if all(known['chunk_id'] != row['chunk_id'] for known in result):
                chunk = graph.chunks[row['chunk_id']]
                result.append({**row, 'full_text': str(_value(chunk, 'text', ''))[:ctx.SOURCE_CHARS],
                               'section_path': list(_value(chunk, 'section_path') or [])})
        return result

    def _bounded_history(self, turns):
        history = deepcopy(turns[-self.settings.assistant_history_turns:])
        for row in history:
            row['answer'] = str(row.get('answer', ''))[:ctx.HISTORY_ANSWER_CHARS]
        limit = self.settings.assistant_history_tokens
        while history and len(stable_json(history)) // 3 > limit:
            candidates = [(len(str(row.get(key, ""))), row, key)
                          for row in history for key in ("question", "answer")]
            size, row, key = max(candidates, key=lambda item: item[0])
            if not size:
                break
            excess = max(1, (len(stable_json(history)) // 3 - limit) * 3)
            row[key] = str(row[key])[:max(0, size - excess)]
        return history

    def _focus(self, graph, node_id, sources, *, owner, doc_id, graph_version):
        """The concept the learner has open: its lecture text (cache only, never generated) and definition passage."""
        node = graph.nodes[node_id]
        module = graph.modules.get(node.get('module_id'), {})
        skeleton = LectureUseCase(None, self.store, settings=self.settings).make(
            doc_id, graph_version, graph, node_id, dry_run=True)
        position = skeleton.get('position', {})
        block = {'node_id': node_id, 'name': node.get('display_name') or node.get('name'),
                 'concept_index': position.get('index_in_module'), 'concept_count': position.get('count_in_module'),
                 'module_id': node.get('module_id') if module else None}
        chunk_id = skeleton.get('definition', {}).get('chunk_id')
        if chunk_id in graph.chunks and all(row['chunk_id'] != chunk_id for row in sources):
            sources.extend(self._shown(graph, [{'chunk_id': chunk_id}]))
        # Lecture text is read from the lecture cache only: no generation, no spend.
        reader = self.content_tools.get('get_lecture')
        lecture = reader(concept=node_id, owner=owner, doc_id=doc_id, graph_version=graph_version,
                         graph=graph, allow_spend=False, cache_only=True) if reader else {}
        if lecture.get('status') == 'ready' and lecture.get('body_md'):
            text = lecture['body_md']
        else:
            text = ' '.join(item['text'] for section in lecture.get('sections', [])
                            for item in section.get('items', [])
                            if lecture.get('status') == 'ready' and item.get('text'))
        text = ctx.strip_lecture_labels(text).strip()[:self.settings.assistant_focus_chars]
        if text:
            block['lecture'] = text
        return block

    def _concept_id(self, graph, value):
        if value in graph.nodes:
            return value
        matches = graph.lookup_concept(value)['matches']
        if len(matches) != 1:
            raise ValueError('Khái niệm không có hoặc có nhiều ứng viên; hãy dùng node_id')
        return matches[0]['node_id']

    def _tool(self, graph, call, *, module, owner, doc_id, graph_version, allow_spend, artifacts,
              session_id=None, session_scope=None, shown=None):
        args = call.args
        name = call.name
        if name == 'search_document':
            hits = self._sources(graph, self._search(graph, args['query'], module,
                                 scope=args.get('scope', 'uu_tien_module'), k=args.get('k', 6)))
            for hit in hits if shown is not None else ():
                shown.setdefault(hit['label'], hit)
            return {'hits': hits}
        if name == 'lookup_concept':
            result = graph.lookup_concept(args['name'])
            return self.concept_lookup(args['name']) if not result['matches'] and self.concept_lookup else result
        if name == 'get_module_info':
            return graph.get_module_info(args['module'], module)
        if name == 'why_here':
            return graph.why_here(self._concept_id(graph, args['concept']), module, settings=self.settings)
        if name == 'path_to':
            return graph.path_to(self._concept_id(graph, args['target']))
        if name == 'traverse':
            return graph.traverse(self._concept_id(graph, args['concept']), args['edge_type'], args.get('direction', 'out'))
        if name == 'get_media':
            return graph.get_media(self._concept_id(graph, args['concept']))
        callback = self.content_tools.get(name)
        if callback is None:
            raise ValueError('Công cụ chưa sẵn sàng')
        if name == 'get_lecture':
            args = {**args, 'concept': self._concept_id(graph, args['concept'])}
        if name in {'make_quiz', 'make_document'}:
            result = callback(**args, owner=owner, doc_id=doc_id, graph_version=graph_version,
                              graph=graph, allow_spend=allow_spend, home_scope=session_scope,
                              session_id=session_id, origin='assistant')
        else:
            result = callback(**args, owner=owner, doc_id=doc_id, graph_version=graph_version,
                              graph=graph, allow_spend=allow_spend)
        if result.get('status') == 'failed':
            reason = result.get('reason') or 'content_generation_failed'
            messages = {
                'scope_too_large': 'Chọn tối đa 5 module hoặc thu hẹp phạm vi để tạo tài liệu.',
                'daily_limit': 'Đã hết hạn mức chi hôm nay; hãy thử lại vào ngày mai.',
                'estimated_cost_over_limit': 'Yêu cầu vượt trần chi; hãy thu hẹp yêu cầu.',
            }
            return {'error': {'code': reason, 'message': messages.get(
                reason, 'Không tạo được nội dung có nguồn trong phạm vi này')}}
        if name == 'get_lecture' and 'body_md' in result:
            artifact = {'kind': 'lecture', 'id': result['lecture_key'], 'node_id': result['node_id']}
            # The lecture numbers its own sources [S1]...; those labels mean nothing to the assistant's [S1].
            summary = {'artifact': artifact, 'status': result.get('status'),
                       'body_md': ctx.strip_lecture_labels(result.get('body_md') or '')}
        elif name == 'get_lecture':
            artifact = {'kind': 'lecture', 'id': result['lecture_key'], 'node_id': result['node_id']}
            items = deepcopy([item for section in result.get('sections', []) for item in section.get('items', [])])
            for item in items:
                labels = {}
                for citation in item.get('citations', []):
                    cid = citation.get('chunk_id')
                    if cid in graph.chunks:
                        labels[citation['label']] = graph.sources.label(cid)
                        citation['label'] = labels[citation['label']]
                item['text'] = REF.sub(lambda match: '[' + labels.get(match[1], match[1]) + ']', item.get('text', ''))
            summary = {'artifact': artifact, 'items': items[:4], 'status': result.get('status')}
            original_refs = result.get('definition', {}).get('formula_refs', [])
            imported_refs = self._register_formulas(graph, original_refs)
            labels = {old['label']: new['label'] for old, new in zip(
                [ref for ref in original_refs if ref.get('image_ref')], imported_refs)}
            for item in summary['items']:
                item['text'] = REF.sub(lambda match: '[' + labels.get(match[1], match[1]) + ']', item.get('text', ''))
                item['formula_labels'] = [labels.get(label, label) for label in item.get('formula_labels', [])]
            summary['formula_refs'] = imported_refs
        elif name == 'make_quiz':
            artifact = {'kind': 'quiz', 'id': result['attempt_id']}
            summary = {'artifact': artifact, 'count': result.get('ready_count', len(result.get('items', [])))}
        else:
            artifact = {'kind': 'document', 'id': result['document_id']}
            summary = {'artifact': artifact, 'title': result.get('title'), 'status': result.get('status')}
        artifacts.append(artifact)
        return summary

    def _register_formulas(self, graph, refs):
        formulas = getattr(graph, 'answer_formulas', {})
        imported = []
        for ref in refs:
            if not ref.get('image_ref'):
                continue
            key = ref.get('occurrence_id') or (ref.get('formula_id'), ref.get('page'))
            existing = next((row for row in formulas.values() if row['_key'] == key), None)
            if existing is None:
                label = 'CT' + str(len(formulas) + 1)
                existing = {**ref, 'label': label, '_key': key}
                formulas[label] = existing
            imported.append({k: v for k, v in existing.items() if k != '_key'})
        graph.answer_formulas = formulas
        return imported

    def ask(self, doc_id, graph_version, session_id, question, *, owner='local',
            client_turn_id=None, allow_spend=False, dry_run=False, on_event=None,
            reminders_enabled=None, focus_node_id=None):
        options = dict(owner=owner, client_turn_id=client_turn_id, allow_spend=allow_spend,
                       dry_run=dry_run, on_event=on_event, reminders_enabled=reminders_enabled,
                       focus_node_id=focus_node_id)
        if not client_turn_id or dry_run:
            return self._ask(doc_id, graph_version, session_id, question, **options)
        generated = False
        def generate():
            nonlocal generated
            generated = True
            return self._ask(doc_id, graph_version, session_id, question, **options)
        key = context_hash([owner, doc_id, session_id, client_turn_id, self.settings.assistant_prompt_version])
        # A failed answer is never kept: "Thử lại" with the same client turn must reach the model again.
        result = self.store.single_flight('assistant-turn:' + key, generate,
                                          cache_if=lambda value: value.get('status') != 'failed',
                                          negative_ttl_seconds=0)
        if not generated and on_event:
            on_event({'event': 'failure' if result.get('status') == 'failed' else 'final', 'answer': result})
        return result

    @staticmethod
    def _plain(messages):
        """Messages without picture bytes: what is hashed and sized."""
        return [{key: ([page for page, _ in value] if key == 'images' else value) for key, value in message.items()}
                for message in messages]

    def _ask(self, doc_id, graph_version, session_id, question, *, owner='local',
             client_turn_id=None, allow_spend=False, dry_run=False, on_event=None, reminders_enabled=None,
             focus_node_id=None):
        if not isinstance(question, str) or not question.strip():
            raise ValueError('Câu hỏi không được rỗng')
        if self.graph.doc_id and self.graph.doc_id != doc_id:
            raise ValueError('Đồ thị không thuộc tài liệu được yêu cầu')
        settings = self.settings
        emit = on_event or (lambda event: None)
        turn_key = context_hash([owner, doc_id, session_id, client_turn_id, settings.assistant_prompt_version]) if client_turn_id else None
        previous = self.store.get_record('answer', turn_key) if turn_key else None
        if previous and not dry_run:
            emit({'event': 'final', 'answer': previous})
            return previous
        graph = LearningGraph(self.graph.payload, list(self.graph.chunks.values()), self.graph.tree)
        graph.graph_version = graph_version
        graph.formula_images = getattr(self.graph, 'formula_images', {})
        graph.parse_version = getattr(self.graph, 'parse_version', None)
        session_record = self.sessions.get(owner, session_id)
        if session_record is None:
            raise KeyError(session_id)
        if session_record.get('doc_id') != doc_id:
            raise ValueError('Phiên không thuộc tài liệu được yêu cầu')
        scope = session_record.get('scope', {"kind": "roadmap"})
        resolved_scope = resolve_scope(scope, graph, settings.scope_remap_min_jaccard)
        current_module_id = resolved_scope['module_id']
        scope_note = "module này đã đổi" if resolved_scope['stale'] else None
        session_state = session_record.get('state', {})
        state = {**self.session_state(doc_id, session_id, owner=owner), **session_state}
        persisted_turns = self.sessions.list_turns(owner, session_id)
        if persisted_turns:
            full_history = [{"question": row["question"],
                             "answer": row.get("answer", {}).get("answer_md", row.get("answer", {}).get("answer", ""))}
                            for row in persisted_turns]
            state['turns'] = self._bounded_history(full_history)
        matches = graph.lookup_concept(question)['matches'][:2]
        followup = (not matches and len(question.split()) <= 8 and bool(state.get('linked_node_ids'))
                    and bool(re.search(r'còn|cái (?:đó|kia|này)|(?:nó|vậy|tiếp)|ví dụ|giải thích thêm', question, re.I)))
        linked = [row['node_id'] for row in matches] or (state.get('linked_node_ids', [])[:2] if followup else [])
        # The focus comes from the browser: it is trusted only if it is a learnable concept of this graph.
        focus_id = focus_node_id if isinstance(focus_node_id, str) and focus_node_id in graph.learnable_nodes else None
        if focus_id and not matches:
            linked = list(dict.fromkeys([focus_id, *(state.get('linked_node_ids', [])[:2] if followup else [])]))[:2]
        if dry_run:
            context = {'scope': self._prompt_scope_card(graph, scope, current_module_id, scope_note),
                       'linked_node_ids': linked, 'question': question, 'history': state['turns']}
            if focus_id:
                context['focus'] = self._focus(graph, focus_id, [], owner=owner, doc_id=doc_id, graph_version=graph_version)
            tokens = len(stable_json(context)) // 3 + 1600
            return {'dry_run': True, 'contract_version': settings.assistant_contract_version,
                    'calls_estimate': [1, settings.assistant_max_rounds],
                    'usd_estimate': estimate_cost(settings.model_id, tokens, settings.assistant_max_output_tokens),
                    'embedding_calls_estimate': 1 if self.search else 0, 'context_hash': context_hash(context),
                    **({'focus_node_id': focus_id} if focus_node_id is not None else {})}
        if not allow_spend and not getattr(self.model, 'is_replay', False):
            raise PermissionError('Trợ lý cần --allow-spend hoặc chế độ phát lại')
        started = perf_counter()
        emit({'event': 'progress', 'text': 'Đang tìm bằng chứng trong tài liệu…'})
        previous_question = state['turns'][-1]['question'] if state.get('turns') else None
        rows = self._search(graph, ctx.search_text(question, previous_question), current_module_id,
                            scope='ca_tai_lieu' if current_module_id is None else 'uu_tien_module', k=6)
        sources = self._shown(graph, rows)
        if not linked and self.concept_lookup:
            lookup = self.concept_lookup(question)
            linked = [item['node_id'] for item in lookup.get('matches', [])][:2]
        focus = self._focus(graph, focus_id, sources, owner=owner, doc_id=doc_id,
                            graph_version=graph_version) if focus_id else None
        progress_rows = self.progress.get_progress(owner, doc_id)['nodes']
        concepts = [{'node_id': nid, 'prerequisites': graph.why_here(nid, current_module_id, settings=settings)['prerequisites'],
                     'path': graph.path_to(nid)} for nid in linked]
        pages = formula_pages([graph.chunks[row['chunk_id']] for row in sources], settings.assistant_max_page_images)
        images = []
        if pages and self.page_images is not None and graph.parse_version is not None:
            images = [(page, data) for page in pages
                      if (data := self.page_images.get(doc_id, int(graph.parse_version), page))]
        bounded_history = self._bounded_history(state['turns'])
        text = ctx.user_message(
            graph, module_id=current_module_id, scope_note=scope_note, concepts=concepts,
            learned={nid: row.get('state') for nid, row in progress_rows.items()}, focus=focus, sources=sources,
            history=bounded_history, question=question)
        prompt = ctx.SYSTEM_PROMPT
        definitions = [item for item in TOOLS if item['name'] not in self.content_tools or self.content_tools[item['name']] is not None]
        definitions_by_name = {item['name']: item for item in definitions}
        messages = [{'role': 'user', 'text': text, **({'images': images} if images else {})}]
        session = self.model.start_session(prompt, definitions)
        shown = {row['label']: row for row in sources}
        cost, input_tokens, output_tokens, thought_tokens, ttft, first_text_s = 0.0, 0, 0, 0, None, None
        model_calls, invalid_calls, logs, artifacts = 0, 0, [], []
        answer, finish_reason = '', None
        exhausted, transport_error, daily_limited, tool_daily_limit = False, None, False, False
        for round_index in range(settings.assistant_max_rounds):
            plain = self._plain(messages)
            tokens = (sum(len(message.get('text') or '') + len(stable_json(message.get('tool_results', [])))
                          for message in plain) + len(prompt)) // 3 + IMAGE_TOKEN_ESTIMATE * len(images)
            estimate = estimate_cost(settings.model_id, tokens, settings.assistant_max_output_tokens)
            if cost + estimate > settings.assistant_max_usd:
                exhausted = True
                break
            replayed = bool(getattr(self.model, 'is_replay', False))
            try:
                with spending_call(self.spend_guard, 'assistant', estimate, owner,
                                   replayed=replayed, clock=self.clock) as admitted_at:
                    final_round = round_index == settings.assistant_max_rounds - 1 or cost + estimate * 2 > settings.assistant_max_usd
                    mode = 'NONE' if final_round else 'AUTO'
                    model_calls += 1
                    raw, calls, usage, turn_id = '', [], {}, None
                    call_ttft = None
                    call_started = perf_counter()
                    try:
                        for event in session.stream(messages, mode=mode):
                            if (call_ttft is None and not replayed
                                    and (isinstance(event, ToolCall) or isinstance(event, Delta) and event.text)):
                                call_ttft = round((perf_counter() - call_started) * 1000)
                            if isinstance(event, Delta):
                                piece = event.text
                                if not piece:
                                    continue
                                if not raw and answer.strip() and not answer.endswith('\n'):
                                    piece = '\n\n' + piece
                                if first_text_s is None and piece.strip():
                                    first_text_s = round(perf_counter() - started, 3)
                                raw += event.text
                                answer += piece
                                emit({'event': 'delta', 'text': piece})
                            elif isinstance(event, ToolCall):
                                calls.append(event)
                            elif isinstance(event, Done):
                                usage = dict(event.usage)
                                turn_id = getattr(event, 'turn_id', None)
                                finish_reason = getattr(event, 'finish_reason', None) or finish_reason
                                if event.ttft_ms is not None:
                                    call_ttft = event.ttft_ms
                    except Exception as error:
                        transport_error = type(error).__name__
                    if not usage:
                        usage = dict(getattr(session, 'last_usage', {}) or {})
                    elapsed = round((perf_counter() - call_started) * 1000)
                    if ttft is None and call_ttft is not None:
                        ttft = round((call_started - started) * 1000) + call_ttft
                    incoming = int(usage.get('promptTokenCount', usage.get('input_tokens', 0)))
                    outgoing = int(usage.get('candidatesTokenCount', usage.get('output_tokens', 0)))
                    thoughts = int(usage.get('thoughtsTokenCount', usage.get('thought_tokens', 0)))
                    call_cost = 0.0 if replayed else token_cost(getattr(self.model, 'model_id', settings.model_id), usage)
                    cost += call_cost
                    input_tokens += incoming
                    output_tokens += outgoing
                    thought_tokens += thoughts
                    self.store.append_usage({**usage_row(purpose='assistant', model_id=self.model.model_id, doc_id=doc_id,
                                             context_hash=context_hash(plain), usage=usage, elapsed_ms=elapsed,
                                             ttft_ms=call_ttft, learner_id=owner, cost_usd=call_cost), 'tool_round': round_index + 1,
                                             'failed': transport_error is not None, 'replayed': replayed,
                                             'created_at': admitted_at})
            except DailyLimitExceeded:
                daily_limited = True
                break
            if transport_error or not calls:
                break
            if mode == 'NONE':
                exhausted = True
                break
            results, round_size = [], 0
            for call in calls:
                tool_started = perf_counter()
                definition = definitions_by_name.get(call.name)
                error = 'Công cụ không được hỗ trợ' if definition is None else _check_args(definition['parameters'], call.args)
                try:
                    if round_size >= settings.tool_results_tokens:
                        error = 'Đã hết ngân sách kết quả công cụ của vòng này'
                    result = {'error': {'code': 'invalid_tool_call', 'message': error}} if error else self._tool(
                        graph, call, module=current_module_id, owner=owner, doc_id=doc_id,
                        graph_version=graph_version, allow_spend=allow_spend, artifacts=artifacts,
                        session_id=session_id, session_scope=scope, shown=shown)
                except (ValueError, KeyError, TypeError, PermissionError) as exception:
                    result = {'error': {'code': 'tool_error', 'message': str(exception)}}
                tool_daily_limit |= isinstance(result, dict) and result.get('error', {}).get('code') == 'daily_limit'
                size = len(stable_json(result)) // 3
                if round_size + size > settings.tool_results_tokens:
                    result = {'error': {'code': 'result_limit', 'message': 'Kết quả vượt giới hạn; hãy thu hẹp yêu cầu'}}
                round_size += len(stable_json(result)) // 3
                invalid_calls += int(isinstance(result, dict) and 'error' in result)
                row = {'name': call.name, 'args': call.args, 'by': 'model', 'result_summary': result,
                       'ms': round((perf_counter() - tool_started) * 1000)}
                logs.append(row)
                emit({'event': 'tool_call', **row})
                emit({'event': 'progress', 'text': f'Đã xử lý công cụ {call.name}.'})
                results.append({'call_id': call.call_id, 'name': call.name, 'result': result})
            messages.extend([{'role': 'model', 'text': raw, 'turn_id': turn_id,
                              'calls': [{'call_id': call.call_id} for call in calls]},
                             {'role': 'tool', 'tool_results': results}])
        else:
            exhausted = True
        failure = None
        if daily_limited or tool_daily_limit:
            status = 'daily_limit'
            if not answer.strip() or tool_daily_limit:
                notice = ('\n\n' if answer.strip() else '') + DAILY_LIMIT_TEXT
                answer += notice
                emit({'event': 'delta', 'text': notice})
        elif answer.strip():
            status = 'answered'
        elif artifacts:
            status, answer = 'answered', ARTIFACT_TEXT
            emit({'event': 'delta', 'text': answer})
        else:
            status = 'failed'
            reason = 'loi_mang' if transport_error else 'het_ngan_sach_cau' if exhausted else 'khong_dung_duoc'
            failure = {'reason_code': reason, 'message': FAILURES[reason], 'retryable': True}
            answer = ''
        graph_cards = {'later_modules': [], 'module_cards': [], 'reminders': [], 'scope_note': scope_note}
        if current_module_id is None:
            graph_cards['roadmap'] = self._scope_card(graph, scope, None, scope_note)['modules']
        enabled = state.get('reminders_enabled', True) if reminders_enabled is None else reminders_enabled
        reminded = set(state.get('reminded_node_ids', []))
        if status == 'answered':
            for nid in linked:
                node = graph.nodes[nid]
                module_id = node.get('module_id')
                if module_id and (current_module_id is None or module_id != current_module_id):
                    module = graph.modules.get(module_id, {})
                    graph_cards['module_cards'].append({'node_id': nid, 'module_id': module_id,
                        'module_index': module.get('index', 0) + 1,
                        'module_title': module.get('title') or module.get('name'),
                        'label': 'nằm ở module' if current_module_id is None else 'nội dung ở module'})
                if current_module_id and graph.relation(module_id, current_module_id) == 'sau':
                    graph_cards['later_modules'].append({'node_id': nid, 'module_id': module_id,
                        'text': f"Học kỹ ở module {graph.modules[module_id].get('index', 0) + 1}"})
                if current_module_id and enabled and not followup:
                    for prerequisite in next(row['prerequisites'] for row in concepts if row['node_id'] == nid):
                        parent = prerequisite['node_id']
                        if (parent not in reminded and parent not in linked and prerequisite.get('quote')
                                and progress_rows.get(parent, {}).get('state') != 'learned'):
                            graph_cards['reminders'].append(prerequisite)
                            reminded.add(parent)
                            if len(graph_cards['reminders']) == 3:
                                break
                if len(graph_cards['reminders']) >= 3:
                    break
        emit({'event': 'graph_card', **graph_cards})
        for artifact in artifacts:
            emit({'event': 'artifact', **artifact})
        seconds_total = round(perf_counter() - started, 3)
        answer_id = str(uuid4())
        validation = {**ctx.build_validation(answer, list(shown)), 'answer_id': answer_id, 'doc_id': doc_id,
                      'session_id': session_id, 'status': status, 'prompt_version': settings.assistant_prompt_version,
                      'rounds': model_calls, 'tools_called': [row['name'] for row in logs],
                      'invalid_tool_calls': invalid_calls, 'images_sent': len(images), 'pages_with_formula': len(pages),
                      'finish_reason': finish_reason, 'transport_error': transport_error,
                      'focus_ignored': focus_node_id is not None and focus_id is None,
                      'seconds_to_first_text': first_text_s, 'seconds_total': seconds_total, 'cost_usd': cost}
        self.store.put_record('assistant_validation', answer_id, validation)
        log.info('assistant validation %s', json.dumps(validation, ensure_ascii=False, sort_keys=True))
        updated_state = {**state, 'reminders_enabled': enabled,
                         'reminded_node_ids': sorted(reminded), 'linked_node_ids': linked}
        result = {'contract_version': settings.assistant_contract_version, 'answer_id': answer_id, 'owner': owner,
                  'doc_id': doc_id, 'graph_version': graph_version, 'session_id': session_id,
                  'client_turn_id': client_turn_id, 'status': status, 'answer_md': answer,
                  'sources': [{'label': label, 'chunk_id': row['chunk_id'], 'page': row.get('page'),
                               'section_path': list(_value(graph.chunks[row['chunk_id']], 'section_path') or [])}
                              for label, row in shown.items()],
                  'graph_cards': graph_cards, 'artifacts': artifacts, 'focus_node_id': focus_id, 'failure': failure,
                  'linked_node_ids': linked, 'tool_calls': logs,
                  'usage': {'model_calls': model_calls, 'input_tokens': input_tokens, 'output_tokens': output_tokens,
                            'thought_tokens': thought_tokens, 'usd': cost, 'ms': round(seconds_total * 1000),
                            'ttft_ms': ttft, 'invalid_tool_calls': invalid_calls,
                            'invalid_tool_call_rate': invalid_calls / max(len(logs), 1)}}
        if status == 'failed':
            emit({'event': 'failure', 'answer': result})
            return result
        history = self._bounded_history([*state['turns'], {'question': question, 'answer': answer}])
        self.store.put_record('assistant_state', self._session_key(doc_id, session_id, owner), {
            **updated_state, 'turns': history})
        session_record['state'] = updated_state
        session_record['updated_at'] = self.clock.now().isoformat()
        self.store.put_record('session', session_id, session_record)
        if turn_key:
            self.store.put_record('answer', turn_key, result)
        self.sessions.append_turn(owner, session_id, question, result, client_turn_id=client_turn_id,
                                  linked_node_ids=linked, artifact_refs=[
                                      {"kind": "quiz" if item["kind"] == "quiz" else "document",
                                       "artifact_id": item["id"]}
                                      for item in artifacts if item.get("kind") in {"quiz", "document"}],
                                  state=updated_state)
        emit({'event': 'final', 'answer': result})
        return result
