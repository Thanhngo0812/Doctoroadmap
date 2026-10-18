"""Generate web handoff contracts by invoking the real B2 use cases, zero network."""
import json
from pathlib import Path

from doc2roadmap.application.phase_b.assistant import AssistantUseCase
from doc2roadmap.application.phase_b.documents import DocumentUseCase
from doc2roadmap.application.phase_b.library import LibraryUseCase
from doc2roadmap.application.phase_b.progress import ProgressUseCase
from doc2roadmap.application.phase_b.sessions import SessionUseCase
from doc2roadmap.application.ports.phase_b import Delta, Done, ToolCall
from doc2roadmap.composition_phase_b import PhaseBRuntime
from doc2roadmap.domain.scope import module_scope
from doc2roadmap.infrastructure.llm.phase_b_demo import DemoModel


def main():
    runtime = PhaseBRuntime(mode='offline', store_path=Path('tmp/b2-contract-examples-store.json'))
    graph = runtime.graph('doc-1', 57)
    store = runtime.store
    owner = 'web-example'
    modules = list(graph.modules)
    home = module_scope(graph, modules[0])
    target = modules[1]
    sessions = SessionUseCase(store, graph)
    session = sessions.create_session(owner, graph.doc_id, home)
    sid = session['session_id']
    documents = DocumentUseCase(DemoModel(), store)
    def make_document(request, scope, **kwargs):
        return documents.create(graph.doc_id, graph.graph_version, graph, request, scope,
                                owner=kwargs['owner'], allow_spend=True,
                                origin='assistant', session_id=kwargs['session_id'], home_scope=kwargs['home_scope'])
    class ScriptedAssistant:
        is_replay = True
        model_id = 'scripted-offline'
        def start_session(self, *args):
            return self
        def stream(self, messages, **kwargs):
            if messages[-1]['role'] == 'user':
                yield ToolCall('make_document', {'request': 'Tóm tắt định nghĩa trong module đã chọn.', 'scope': target}, 'example-document')
            else:
                yield Delta('')
            yield Done({})
    answer = AssistantUseCase(graph, store, ScriptedAssistant(), document=make_document).ask(
        graph.doc_id, graph.graph_version, sid, 'Tạo tài liệu về module tiếp theo.',
        owner=owner, allow_spend=True, client_turn_id='example-turn')
    progress = ProgressUseCase(store, graph)
    node_id = graph.modules[modules[0]]['node_ids'][0]
    progress.set_progress(owner, graph.doc_id, node_id, True)
    library = LibraryUseCase(store, graph)
    here = library.list_library(owner, graph.doc_id, 'module:' + modules[0])
    elsewhere = library.list_library(owner, graph.doc_id, 'module:' + target)
    document_id = next((item['id'] for item in here['items'] if item['kind'] == 'document'), None)
    if not document_id:
        raise AssertionError('actual assistant did not create the expected document')
    assert any(item['id'] == document_id and item['group'] == 'elsewhere' for item in elsewhere['items'])
    quiz = runtime.quiz(graph).make_quiz(graph.doc_id, owner=owner, scope={'kind': 'roadmap'}, seed=44)
    populated_session = sessions.get(owner, sid)
    turns = sessions.list_turns(owner, sid)
    sessions.delete_session(owner, sid)
    after_delete = library.list_library(owner, graph.doc_id, 'module:' + modules[0])
    assert any(item['id'] == document_id and item.get('session_deleted') for item in after_delete['items'])
    replay = json.loads(Path('tmp/phaseb-sa43-replay-20261018.json').read_text(encoding='utf-8'))
    output = {'scope-1': home, 'session-1': populated_session, 'turn-1': turns[0],
              'library-1': {'here': here, 'elsewhere': elsewhere, 'after_session_delete': after_delete},
              'progress-1': progress.get_progress(owner, graph.doc_id),
              'lecture-2': replay['completed'][5]['arms'][0]['result'],
              'lecture-2-failed': replay['completed'][8]['arms'][0]['result'],
              'answer-2': answer, 'quiz-2': quiz,
              'document-2': documents.get(document_id, owner=owner),
              'verification': {'network_calls': 0, 'new_usd': 0,
                               'same_document_here_elsewhere': True, 'delete_session_preserves_document': True}}
    Path('report/pha-b2-contract-examples-2026-10-18.json').write_text(
        json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'contracts': list(output), 'quiz_items': quiz['ready_count'],
                      'quiz_modules': len({graph.nodes[n]['module_id'] for n in quiz['node_ids']}),
                      'document_status': output['document-2']['status'], 'new_usd': 0}))


if __name__ == '__main__':
    main()
