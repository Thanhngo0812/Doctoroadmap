"""Explicitly offline demonstration model; no network or API credentials."""
import json
import re
from types import SimpleNamespace

from doc2roadmap.application.ports.phase_b import Delta, Done, ToolCall


def _json(text):
    start = text.find('{')
    return json.JSONDecoder().raw_decode(text[start:])[0] if start >= 0 else {}


_PASSAGE = re.compile(r'^\[(S\d+)\] \(trang [^\n]*\)\n(.*?)(?=^\[S\d+\] \(trang |^Hội thoại trước:|^Câu hỏi của người học:|\Z)',
                      re.M | re.S)


def _context(text):
    """The assistant sends the model prose (answer-3); older callers still send a JSON context."""
    if text.lstrip().startswith('{'):
        return _json(text)
    body = text.split('Tư liệu từ sách:', 1)[-1]
    question = text.rsplit('Câu hỏi của người học:', 1)[-1].strip()
    return {'question': question, 'scope': {'kind': 'roadmap'},  # the prose names no module id: tools run on the roadmap
            'sources': [{'label': label, 'text': passage.strip()} for label, passage in _PASSAGE.findall(body)]}


class DemoModel:
    is_replay = True
    model_id = 'demo-offline'

    def start_session(self, system_prompt, tools=()):
        return DemoSession(system_prompt, tools)


class DemoSession:
    def __init__(self, prompt, tools):
        self.prompt, self.tools = prompt, tools
        self.last_usage, self.last_finish_reason, self.last_ttft_ms = {}, 'STOP', 0

    def _payload(self, prompt, schema):
        data = _json(prompt)
        properties = schema.get('properties', {})
        if 'title' in properties and 'description' in properties:
            title = (data.get('author_path') or [data['concepts'][0]['display_name']])[-1]
            return {'title': title, 'description': [{'text': data['concepts'][0]['display_name'],
                                                    'node_ids': [data['concepts'][0]['node_id']]}]}
        sources = data.get('sources', {})
        first = next(iter(sources.items()), (None, {}))
        label, source = first
        text = source.get('text', '')
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n+', text) if s.strip()]
        quote = (sentences or [text])[0][:190]
        if 'markdown' in properties:
            return {'title': 'Tài liệu ôn tập', 'markdown': f'{quote} [{label}]' if label else '',
                    'citations': [{'label': label, 'quote': quote}] if label else [], 'outside_document_blocks': []}
        items = [{'text': sentence[:190], 'sources': [label], 'quote': sentence[:190]}
                 for sentence in sentences[:3]] if label else []
        return {'prereq_notes': [], 'explanation': items, 'example': [], 'contrasts': [],
                'self_check': None, 'gaps': []}

    def ask_json(self, prompt, *, response_schema):
        return SimpleNamespace(payload=self._payload(prompt, response_schema), usage={}, raw_text='')

    def stream_json(self, prompt, *, response_schema):
        text = json.dumps(self._payload(prompt, response_schema), ensure_ascii=False)
        for index in range(0, len(text), 31):
            yield text[index:index + 31]

    def stream(self, messages, *, mode='AUTO'):
        context = _context(messages[0].get('text', '{}'))
        question = context.get('question', '')
        tools = {item['name'] for item in self.tools}
        if messages[-1]['role'] == 'user' and mode == 'AUTO':
            scope = context.get('scope', {})
            module = scope.get('module') or {}
            nodes = module.get('node_ids', [])
            tool_scope = module.get('module_id') if scope.get('kind') == 'module' else 'roadmap'
            if re.search(r'quiz|trắc nghiệm|câu hỏi ôn', question, re.I) and 'make_quiz' in tools:
                yield ToolCall('make_quiz', {'scope': tool_scope, 'n': 5}, 'demo-quiz')
                yield Done({})
                return
            if re.search(r'tạo.*tài liệu|đề cương|bản chi tiết', question, re.I) and 'make_document' in tools:
                yield ToolCall('make_document', {'request': question, 'scope': tool_scope}, 'demo-document')
                yield Done({})
                return
            if re.search(r'bài giảng|giảng cho', question, re.I) and nodes and 'get_lecture' in tools:
                concept = (context.get('concepts') or [{'node_id': nodes[0]}])[0]['node_id']
                yield ToolCall('get_lecture', {'concept': concept}, 'demo-lecture')
                yield Done({})
                return
        sources = context.get('sources', [])
        ignored = {'là', 'gì', 'của', 'tôi', 'hãy', 'cho', 'về', 'không', 'như', 'thế', 'nào',
                   'còn', 'cái', 'kia', 'thì', 'sao', 'và', 'trong', 'được', 'một', 'những', 'với', 'bạn'}
        terms = {word.casefold() for word in re.findall(r'\w+', question) if len(word) > 2} - ignored
        evidence = ' '.join(source.get('text', '') for source in sources).casefold()
        if terms and not any(re.search(r'(?<!\w)' + re.escape(term) + r'(?!\w)', evidence) for term in terms):
            sources = []
        if sources:
            source = sources[0]
            text = re.split(r'(?<=[.!?])\s+|\n+', source['text'])[0][:500]
            yield Delta(text + f" [{source['label']}]")
        else:
            yield Delta('Tài liệu không có đoạn nào khớp với câu hỏi này.')
        yield Done({})
