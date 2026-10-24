"""Learner projection: no tool arguments, internal URLs, costs or admin validation."""
from wayfinder.application.lecture_view import pick


TOOL_LABELS = {
    'search_document': 'Đang tìm trong tài liệu…', 'lookup_concept': 'Đang tìm bài học…',
    'get_module_info': 'Đang xem module…', 'why_here': 'Đang xem bài cần học trước…',
    'path_to': 'Đang xem lộ trình…', 'traverse': 'Đang tìm bài liên quan…',
    'get_media': 'Đang xem hình trong tài liệu…', 'get_lecture': 'Đang đọc bài đã có…',
    'make_quiz': 'Đang tạo quiz…', 'make_document': 'Đang tạo tài liệu…',
}


def session_view(row):
    return {**pick(row, ('contract_version', 'session_id', 'title', 'created_at', 'updated_at', 'turn_count',
        'last_question_preview', 'resolved_module_id', 'module_label', 'scope_note')),
        'scope': pick(row.get('scope', {}), ('kind', 'module_id_at_creation'))}


def cards_view(raw, graph):
    cards = {'scope_note': raw.get('scope_note') if raw.get('scope_note') == 'module này đã đổi' else None}
    for name in ('module_cards', 'later_modules'):
        cards[name] = [pick(row, ('node_id', 'module_id', 'module_index', 'module_title', 'title', 'label', 'text'))
            for row in raw.get(name, []) if row.get('module_id') in graph.modules]
    cards['roadmap'] = [{'module_id': mid, 'module_index': module.get('index', 0) + 1,
        'module_title': module.get('title') or module.get('name', '')}
        for row in raw.get('roadmap', []) for mid, module in graph.modules.items()
        if row.get('index') == module.get('index', 0) + 1]
    cards['reminders'] = [pick(row, ('node_id', 'name', 'module_id', 'module_index', 'module_title', 'quote', 'page', 'learner_status'))
        for row in raw.get('reminders', []) if row.get('node_id') in graph.learnable_nodes]
    return cards


def answer_view(raw, course, graph, artifacts):
    if raw.get('contract_version') != 'answer-3':
        raise ValueError('W09 requires answer-3')
    result = pick(raw, ('contract_version', 'answer_id', 'session_id', 'client_turn_id', 'status', 'answer_md', 'focus_node_id'))
    result.update(course_id=course.id, doc_id=course.doc_id, graph_version=course.published_graph_version,
        sources=[pick(row, ('label', 'chunk_id', 'page', 'section_path')) for row in raw.get('sources', [])],
        graph_cards=cards_view(raw.get('graph_cards', {}), graph), artifacts=artifacts,
        warnings=[],
        failure=pick(raw['failure'], ('reason_code', 'message', 'retryable')) if raw.get('failure') else None)
    return result
