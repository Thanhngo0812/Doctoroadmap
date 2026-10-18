import json
from types import SimpleNamespace as NS

import pytest

from doc2roadmap.composition_phase_b import PhaseBRuntime
from doc2roadmap.config import Settings
from doc2roadmap.domain.models import Chunk, ChunkingResult, DocumentNode, DocumentTree, Section


@pytest.fixture
def named_runtime(tmp_path):
    runtime = PhaseBRuntime(settings=Settings(artifact_dir=tmp_path, _env_file=None), mode='gemini', allow_spend=True)
    store = runtime.artifacts
    names = ['Ma trận', 'Định thức']
    aliases = ['Bảng số', 'Đại lượng']
    sections, chunks, nodes, modules = [], [], [], []
    for i, name in enumerate(names):
        text = name + ' là ' + aliases[i] + '.'
        sections.append(Section(f's{i}', 'book', f'2.{i + 1} {name}', 1, 1, None, [name], i))
        chunks.append(Chunk(f'c{i}', 'book', i, 0, 1, 0, len(text), f's{i}', [name], 1,
                            ['text'], text, None, [], 10, 'test'))
        nodes.append({'node_id': f'n{i}', 'name': name, 'description': aliases[i],
                      'aliases': [aliases[i]], 'learnable': True, 'teaching_chunk_ids': [f'c{i}'],
                      'module_id': f'm{i}'})
        modules.append({'module_id': f'm{i}', 'index': i, 'title': name, 'node_ids': [f'n{i}'],
                        'title_section_ids': [f's{i}'], 'module_dependencies': []})
    parse = store.save_parse('book', 'source', 'parser', 'parse', {}, DocumentTree([DocumentNode('text', '', 0)]))
    stored_chunks = store.save_chunks('book', 'source', 'chunks', {}, parse.version,
                                      ChunkingResult('book', sections, chunks, ''))
    store.save_graph('book', 'source', 'a10', {'chunks_version': stored_chunks.version},
                     {'stage': 'stages', 'nodes': nodes, 'modules': modules,
                      'sequence': ['n0', 'n1'], 'requires_edges': []},
                     upstream_version=None, manifest_fields={'stage': 'stages'})

    class Model:
        model_id = runtime.b_settings.model_id

        def __init__(self):
            self.calls = 0

        def start_session(self, prompt):
            return self

        def ask_json(self, prompt, *, response_schema):
            self.calls += 1
            index = int(json.loads(prompt)['module_id'][1:])
            return NS(payload={'title': aliases[index], 'description': [
                {'text': names[index], 'node_ids': [f'n{index}']}]}, usage={}, raw_text='')

    model = Model()
    runtime.model = lambda purpose: model
    first = runtime.naming('book', graph_version=1)
    assert model.calls == 2
    assert [m['title'] for m in first['modules']] == aliases
    return runtime, model, first['graph_version']


def test_repeating_default_naming_reuses_original_a10_context_without_more_model_calls(named_runtime):
    runtime, model, _ = named_runtime
    assert runtime.naming('book', dry_run=True)['calls_estimate'] == 0
    result = runtime.naming('book')
    assert result['reused']
    assert model.calls == 2


def test_explicit_named_graph_still_uses_its_changed_neighbor_context(named_runtime):
    runtime, model, named_version = named_runtime
    assert runtime.naming('book', graph_version=named_version, dry_run=True)['calls_estimate'] == 2
    assert model.calls == 2


@pytest.mark.parametrize('source_version', [None, 0, 999])
def test_invalid_naming_lineage_stops_before_model_work(named_runtime, source_version):
    runtime, model, named_version = named_runtime
    named = runtime.artifacts.load_graph('book', named_version)
    runtime.artifacts.save_graph('book', 'source', 'invalid-lineage',
        {**named.manifest['config'], 'upstream_version': source_version}, named.payload,
        upstream_version=named_version, manifest_fields={'stage': 'stages'})
    with pytest.raises(ValueError, match='A10 đầu vào'):
        runtime.naming('book', dry_run=True)
    assert model.calls == 2
