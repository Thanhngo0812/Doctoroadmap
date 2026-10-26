"""Explicit learner projections; never serialize a private attempt or usage."""
from wayfinder.application.lecture_view import pick


def quiz_item(row):
    return {**pick(row, ('item_id', 'concept_id', 'module_id', 'generator', 'bloom', 'stem')),
        'options': [pick(option, ('option_id', 'text')) for option in row.get('options', [])]}


def quiz_view(row, course, source=None):
    return {**pick(row, ('contract_version', 'attempt_id', 'status', 'created_at', 'ready_count', 'total_concepts')),
        'course_id': course.id, 'items': [quiz_item(item) for item in row.get('items', [])],
        'module_id': row.get('module_id'), 'source_document': source, 'submitted': bool(row.get('submission'))}


def result_view(row):
    return {**pick(row, ('contract_version', 'attempt_id', 'correct_count', 'question_count', 'submitted_at')),
        'results': [{**pick(item, ('item_id', 'concept_id', 'stem', 'selected_option_id', 'is_correct', 'explanation', 'why_wrong')),
            'correct_option': pick(item.get('correct_option', {}), ('text',)),
            'evidence': [pick(source, ('label', 'chunk_id', 'page')) for source in item.get('evidence', [])]}
            for item in row.get('results', [])]}


def document_view(row, course, source=None):
    return {**pick(row, ('contract_version', 'document_id', 'title', 'markdown', 'status', 'created_at', 'request')),
        'course_id': course.id, 'sources': [pick(item, ('label', 'chunk_id', 'page', 'section_path')) for item in row.get('sources', [])],
        'warnings': ['cat_ngan'] if 'cat_ngan' in row.get('warnings', []) else [],
        'failure': pick(row['failure'], ('reason_code', 'message', 'retryable')) if row.get('failure') else None,
        'source_document': source}
