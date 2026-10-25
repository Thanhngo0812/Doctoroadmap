"""The learner projection of lecture-3; cache diagnostics stay on the server."""
from urllib.parse import quote


def pick(value, keys):
    return {key: value[key] for key in keys if key in value}


def citation(value):
    return pick(value, ('label', 'chunk_id', 'page', 'section_path', 'quote', 'char_start', 'char_end')) if value else None


def public_lecture(raw, course, graph, progress, media=None):
    if raw.get('contract_version') != 'lecture-3':
        raise ValueError('W08 requires lecture-3; legacy lectures cannot be served')

    def state(node_id):
        return progress.get(node_id, {}).get('state', 'not_learned')

    module_numbers = {row['module_id']: index for index, row in enumerate(
        sorted(graph.modules.values(), key=lambda row: row.get('index', 0)), 1)}

    def definition(value):
        result = pick(value, ('quote', 'chunk_id', 'page'))
        result['citation'] = citation(value.get('citation'))
        result['formula_refs'] = []
        for ref in value.get('formula_refs', []):
            asset = pick(ref, ('label', 'formula_id', 'occurrence_id', 'page'))
            key = media.asset_key(graph, ref) if media else None
            if key:
                asset.update(asset_key=key, url=f'/api/v1/courses/{course.id}/media/{quote(key, safe="/")}')
            result['formula_refs'].append(asset)
        return result

    result = pick(raw, ('status', 'lecture_key', 'node_id', 'body_md'))
    if result.get('status') == 'not_cached':
        result['status'] = 'generating'
    result.update(contract_version='lecture-3', course_id=course.id, doc_id=course.doc_id,
        graph_version=course.published_graph_version,
        position=pick(raw.get('position', {}), ('module_id', 'module_index', 'index_in_module',
            'count_in_module', 'previous_node_id', 'next_node_id')),
        definition=definition(raw.get('definition', {})), prerequisites=[], next_up=[],
        sources=[pick(row, ('label', 'chunk_id', 'page', 'section_path')) for row in raw.get('sources', [])],
        self_check=pick(raw['self_check'], ('question_md', 'answer_md')) if raw.get('self_check') else None,
        warnings=[w for w in raw.get('warnings', []) if w in {'cat_ngan', 'khong_co_doan_day', 'thieu_cong_thuc'}],
        usage=pick(raw.get('usage', {}), ('model_calls', 'input_tokens', 'output_tokens', 'cost_usd')),
        failure=None, media=[], source_document=media.describe_source(course, graph) if media else None)
    for row in raw.get('prerequisites', []):
        recall = row.get('recall', {})
        result['prerequisites'].append({'recall': {
            **pick(recall, ('node_id', 'name', 'module_index', 'module_title', 'order_note')),
            'module_id': graph.nodes.get(recall.get('node_id'), {}).get('module_id'),
            'module_number': module_numbers.get(graph.nodes.get(recall.get('node_id'), {}).get('module_id')),
            'definition': definition(recall.get('definition', {}))},
            'learner_status': state(recall.get('node_id'))})
    for row in raw.get('next_up', []):
        nid = row.get('node_id')
        if nid not in graph.learnable_nodes:
            continue
        result['next_up'].append({**pick(row, ('node_id', 'name', 'module_index', 'module_title', 'quote')),
            'module_id': graph.nodes[nid].get('module_id'), 'citation': citation(row.get('citation')),
            'module_number': module_numbers.get(graph.nodes[nid].get('module_id')),
            'learner_status': state(nid)})
    for row in raw.get('media', []):
        for key in (media.media_keys(graph, row) if media else []):
            result['media'].append({'asset_key': key, 'caption': row.get('caption') or row.get('name') or '',
                'url': f'/api/v1/courses/{course.id}/media/{quote(key, safe="/")}'})
    if raw.get('failure'):
        result['failure'] = {**pick(raw['failure'], ('reason_code', 'message', 'ask_assistant')),
            'retryable': True, 'read_page': pick(raw['failure'].get('read_page') or {}, ('page', 'chunk_id'))}
    if result['status'] in {'failed', 'no_source'}:
        result['failure'] = result['failure'] or {'reason_code': 'khong_co_nguon', 'read_page': {'page': result['definition'].get('page')}, 'ask_assistant': True}
        result['failure']['retryable'] = True
        if not result['failure'].get('message'):
            result['failure']['message'] = 'Chưa thể soạn bài học này. Bạn có thể đọc tài liệu hoặc thử lại.'
    return result
