"""Frozen pre-19n artifacts; no retired stage is needed to construct this fixture."""
import json
from pathlib import Path

from tests.unit.application.test_a4_pipeline import fixture_store

DOC = 'baocao-canhan'
FIXTURE = Path('tests/fixtures/legacy-v3/baocao-canhan.json')


def legacy_store(tmp_path):
    store = fixture_store(tmp_path)
    frozen = json.loads(FIXTURE.read_text(encoding='utf-8'))
    for name, artifact in (('canonical', frozen['canonical']), ('graph', frozen['identity'])):
        path = store.root / name / DOC / f"v{artifact['manifest']['version']}"
        store._write(path / 'manifest.json', artifact['manifest'])
        store._write(path / f'{name}.json', artifact['payload'])
    return store, store.load_latest_graph(DOC), frozen


def real_upstream(tmp_path):
    from types import SimpleNamespace
    from doc2roadmap.domain.canonical import digest
    store, _, frozen = legacy_store(tmp_path)
    canonical = store.load_latest_canonical(DOC)
    config = {'chunks_version': store.load_latest_candidates(DOC).manifest['upstream_version'],
              'canonical_version': canonical.version}
    return store, SimpleNamespace(payload={**canonical.payload, 'stage': 'provenance', 'mention_map': {}},
        version=canonical.version, manifest={'config': config, 'config_hash': digest(config)})
