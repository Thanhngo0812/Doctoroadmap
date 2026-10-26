"""Read only the approved doc-6 copy; do not run a build or import learner caches."""
from hashlib import sha256
from copy import deepcopy
from inspect import signature
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'src/web/backend')]

from doc2roadmap.application.phase_b.retrieval import assert_retrieval_compatible, load_learning_graph
from doc2roadmap.composition_build import DocumentPipeline
from doc2roadmap.config import Settings
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore
from wayfinder.domain.file_paths import safe_path
from wayfinder.infrastructure.real_build import CoreBuildPortUnavailable, RealBuildRuntime
from wayfinder.settings import WebSettings


def main():
    manifest = ROOT / 'report/doc1-rebuild-evidence-2026-10-20/development-fixtures.json'
    assert sha256(manifest.read_bytes()).hexdigest() == '5fc819f723f7263fe3d443ec780009a75aae66f2c35db8fe0bc3e3c50464eb84'
    entries = [row for row in json.loads(manifest.read_text(encoding='utf-8'))['files']
               if '/doc-6/' in row['path'] or row['path'] == 'doc-6.pdf']
    before = {}
    for row in entries:
        path = safe_path(ROOT, row['path'])
        assert not path.is_symlink() and path.stat().st_nlink == 1, row['path']
        before[row['path']] = sha256(path.read_bytes()).hexdigest()
        assert before[row['path']] == row['sha256'], row['path']
    store = JsonArtifactStore(ROOT / 'artifacts')
    graph = store.load_graph('doc-6', 29)
    learning = load_learning_graph(store, 'doc-6', 29)
    chunk_version = graph.manifest['config']['chunks_version']
    chunks = store.load_chunks('doc-6', chunk_version)
    parsed = store.load_parse('doc-6', chunks.manifest['parse_version'])
    index = store.load_latest_retrieval('doc-6')
    fingerprint = assert_retrieval_compatible(index.payload, list(learning.chunks.values()))
    wrong_index = deepcopy(index.payload)
    wrong_index['documents'][0]['text'] += ' changed only in memory'
    try:
        assert_retrieval_compatible(wrong_index, list(learning.chunks.values()))
    except ValueError:
        changed_text_rejected = True
    else:
        raise AssertionError('Retrieval compatibility guard did not reject changed text')
    source_sha = sha256((ROOT / 'doc-6.pdf').read_bytes()).hexdigest()
    assert source_sha == parsed.manifest['source_hash']

    def forbidden(*args, **kwargs):
        raise AssertionError('No providers, ADC, SMTP, Cloudinary or CLI stores in preflight')
    targets = ('google.auth.default', 'doc2roadmap.infrastructure.llm.gemini.urlopen',
               'doc2roadmap.infrastructure.embedding.gemini.urlopen',
               'doc2roadmap.infrastructure.google_auth.VertexCredentials.headers',
               'doc2roadmap.infrastructure.artifacts.phase_b_store.JsonPhaseBStore.__init__',
               'doc2roadmap.infrastructure.artifacts.build_log.SqliteBuildLog.__init__',
               'smtplib.SMTP', 'wayfinder.infrastructure.media.CloudinaryMediaStore')
    from contextlib import ExitStack
    with ExitStack() as guards:
        for target in targets:
            guards.enter_context(patch(target, forbidden))
        # A missing port must be rejected before even looking at the engine.
        try:
            RealBuildRuntime(WebSettings(_env_file=None), None, core_settings=Settings(
                _env_file=None, llm_transport='vertex', vertex_project='preflight-no-network', vertex_location='global'))
        except CoreBuildPortUnavailable:
            port_state = 'missing on main; stopped before engine/provider'
        else:
            raise AssertionError('Port is now available: run the post-SA-62 checks instead')
    assert 'phase_b_store' not in signature(DocumentPipeline).parameters
    assert all(sha256((ROOT / relative).read_bytes()).hexdigest() == digest for relative, digest in before.items())
    result = {'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'verified_doc6_files': len(entries), 'input_files_unchanged': True,
              'source_doc_id': 'doc-6', 'source_graph_version': 29,
              'chunks_version': chunks.version, 'parse_version': parsed.version,
              'retrieval_version': index.version, 'source_sha256': source_sha,
              'source_parser': parsed.manifest['config']['parser'],
              'graph_modules': len(learning.modules), 'graph_chunks': len(learning.chunks),
              'retrieval_compatible_with_source_graph': True, 'retrieval_input_fingerprint': fingerprint,
              'retrieval_changed_text_rejected': changed_text_rejected,
              'web_doc_id': 'u-' + source_sha[:20],
              'direct_web_identity_artifacts': {kind: (ROOT / 'artifacts' / kind / ('u-' + source_sha[:20])).exists()
                  for kind in ('parse_tree', 'chunks', 'candidates', 'canonical', 'graph', 'retrieval')},
              'source_graph_available': True, 'web_pipeline_cache_hit_proven': False,
              'generation_cache': 'unknown; learner store not read',
              'embedding_cache': 'unknown; learner store not read',
              'core_port_preflight': port_state, 'real_dry_run_executed': False,
              'collector_receipts': 0, 'queue_claims': 0, 'provider_calls': 0,
              'new_spend_usd': 0, 'snapshot_modified': False}
    (Path(__file__).parent / 'result.json').write_bytes((json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode())
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
