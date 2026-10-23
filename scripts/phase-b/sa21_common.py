"""SA-21 shared helpers: pinned graphs (read-only), isolated runtimes per configuration, sample classification.

Nothing here writes to the shared artifacts directory. Settings are read from the shared .env, graphs and formula images are
read from the shared artifacts directory, and every output goes to tmp/ of this worktree.
"""
from __future__ import annotations

import base64
import dataclasses
import glob
import hashlib
import json
from pathlib import Path

from doc2roadmap.application.phase_b.lectures import _assemble, _formula_refs
from doc2roadmap.application.phase_b.retrieval import load_learning_graph
from doc2roadmap.composition_phase_b import PhaseBRuntime
from doc2roadmap.config import Settings
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore

WORKTREE = Path(__file__).resolve().parents[2]
SHARED = Path('C:/Users/ngoco/Desktop/Doctoroadmap')
OUT = WORKTREE / 'tmp/sa21'
MODEL_ID = 'gemini-3.1-flash-lite'
CAP_USD = 5.0
OPTIONAL_USD_LIMIT = 3.5
PINS = {'doc-1': 8, 'nhap-mon-ml': 50, 'naive-bayes': 49, 'doc-6': 29, 'xstk-ch3-1': 68, 'doc-4': 27}
EXPECTED = {'doc-1': (35, 223), 'nhap-mon-ml': (15, 75), 'naive-bayes': (5, 33), 'doc-6': (2, 11),
            'xstk-ch3-1': (14, 82), 'doc-4': (91, 495)}
STRATA = {'doc-1': 15, 'xstk-ch3-1': 10, 'doc-4': 15, 'nhap-mon-ml': 5, 'naive-bayes': 3, 'doc-6': 2}
SEEDS = {'sample': 20261031, 'trial': 20261032, 'codes': 20261033, 'y_codes': 20261034,
         'variant_labels': {'C1': 5011, 'C2': 6021}, 'order': {'C1': 5012, 'C2': 6022}, 'y_order': {'C1': 5013, 'C2': 6023}}
CONFIGS = ('A0', 'A1', 'A2', 'A3', 'A4')
STORE_NAMES = {'A1': 'store-A1.json', 'A2': 'store-A2.json', 'A3': 'store-A3.json', 'A4': 'store-A4.json'}
APPROVAL = '"tiền duyệt" (chủ dự án, 2026-10-22; trần SA-21 là 5 USD)'


def settings():
    return Settings(_env_file=SHARED / '.env', artifact_dir=SHARED / 'artifacts')


def b_settings(config):
    base = BSettings(model_id=MODEL_ID)
    if config == 'A4':
        return dataclasses.replace(base, lecture_temperature=1.0)
    return base


def artifact_store():
    return JsonArtifactStore(SHARED / 'artifacts')


def load_graphs():
    store = artifact_store()
    graphs = {}
    for doc_id, version in PINS.items():
        graph = load_learning_graph(store, doc_id, version)
        modules, learnable = EXPECTED[doc_id]
        if len(graph.modules) != modules or len(graph.learnable_nodes) != learnable:
            raise RuntimeError(f'{doc_id}: graph differs from the pin')
        graphs[doc_id] = graph
    return graphs


def make_runtime(config):
    OUT.mkdir(parents=True, exist_ok=True)
    runtime = PhaseBRuntime(settings=settings(), b_settings=b_settings(config), allow_spend=True, mode='gemini',
                            store_path=OUT / STORE_NAMES[config])
    runtime.record_dir = None  # never the shared recordings directory
    if runtime.settings.llm_transport != 'vertex':
        raise RuntimeError('SA-21 requires the configured Vertex transport')
    return runtime


def formula_inside(graph, citation):
    """Indexes of the chunk's formulas that sit inside a cited span."""
    chunk = graph.chunks.get((citation or {}).get('chunk_id'))
    if chunk is None or not chunk.formula_refs:
        return []
    start, end = citation.get('char_start', 0), citation.get('char_end', 0)
    return [i for i, ref in enumerate(chunk.formula_refs) if start <= ref.char_start < end]


def formula_png(doc_id, media_id):
    found = glob.glob(str(SHARED / 'artifacts/phase_b/formula_images' / doc_id / 'parse-v*/images' / f'{media_id}.png'))
    return base64.b64encode(Path(found[0]).read_bytes()).decode('ascii') if found else None


def chunk_formula_images(graph, chunk_id, only_inside=None):
    """Base64 PNGs for the formulas of one chunk (optionally only those at the given indexes)."""
    chunk = graph.chunks.get(chunk_id)
    if chunk is None or not chunk.formula_refs:
        return []
    refs = _formula_refs(graph, [chunk_id])
    if len(refs) != len(chunk.formula_refs):
        return []
    out = []
    for i, ref in enumerate(refs):
        if only_inside is not None and i not in only_inside:
            continue
        png = formula_png(graph.doc_id, ref['media_id']) if ref.get('media_id') else None
        if png:
            out.append({'png': png, 'text': ref.get('raw_text') or ''})
    return out


def definition_formula_images(graph, definition):
    """Formula images inside the definition sentence of a skeleton's `definition`."""
    citation = {'chunk_id': definition.get('chunk_id'), **(definition.get('citation') or {})}
    inside = formula_inside(graph, citation)
    return chunk_formula_images(graph, definition.get('chunk_id'), set(inside)) if inside else []


def classify(graph, node_id):
    """Cheap, no network: the sample strata of one concept, or None when it has no teaching source."""
    context, skeleton, _ = _assemble(graph, node_id, b_settings('A2'))
    if not context['teaching'] and not context['extra_definitions']:
        return None
    return {'has_formula': bool(formula_inside(graph, {'chunk_id': skeleton['definition'].get('chunk_id'),
                                                       **(skeleton['definition'].get('citation') or {})})),
            'has_prereq': bool(skeleton['prerequisites']),
            'bridge_candidates': len(context['bridge_candidates']),
            'next_up': len(skeleton['next_up'])}


def concept_name(graph, node_id):
    node = graph.nodes[node_id]
    return node.get('display_name') or node.get('name') or ''


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=1, sort_keys=True, default=str) + '\n', encoding='utf-8')


def result_path(config, node_id):
    return OUT / 'results' / config / (hashlib.sha1(node_id.encode()).hexdigest()[:20] + '.json')
