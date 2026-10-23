"""SA-22 shared helpers: pinned graphs (read-only), runtime on an isolated store, and a use case that records every candidate.

Nothing here writes to the shared artifacts directory. Settings are read from the shared .env, artifacts are read from
the shared artifacts directory, and every output goes to tmp/ of this worktree.
"""
from __future__ import annotations

import copy
import hashlib
import random
import threading
from pathlib import Path

from doc2roadmap.application.phase_b.quiz import QuizUseCase
from doc2roadmap.application.phase_b.retrieval import load_learning_graph
from doc2roadmap.composition_phase_b import PhaseBRuntime
from doc2roadmap.config import Settings
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore

WORKTREE = Path(__file__).resolve().parents[2]
SHARED = Path('C:/Users/ngoco/Desktop/Doctoroadmap')
OUT = WORKTREE / 'tmp/sa22'
STORE_PATH = OUT / 'sa22-store.json'
MODEL_ID = 'gemini-3.1-flash-lite'
PINS = {'doc-1': 8, 'nhap-mon-ml': 50, 'naive-bayes': 49, 'doc-6': 29, 'xstk-ch3-1': 68, 'doc-4': 27}
EXPECTED = {'doc-1': (35, 223), 'nhap-mon-ml': (15, 75), 'naive-bayes': (5, 33), 'doc-6': (2, 11),
            'xstk-ch3-1': (14, 82), 'doc-4': (91, 495)}
# Concepts per book, report section 5.2 (doc-6 has only 11 learnable concepts, so "at most what exists").
STRATA = {'doc-1': 30, 'doc-4': 30, 'xstk-ch3-1': 20, 'nhap-mon-ml': 20, 'naive-bayes': 10, 'doc-6': 10}
SEEDS = {'sample': 20261023, 'rng': 20261024, 'trial': 20261025, 'trial_codes': 20261026, 'rejected_cap': 20261027,
         'C1': {'order': 3011}, 'C2': {'order': 4021}}
OWNER = 'sa22'


def settings():
    return Settings(_env_file=SHARED / '.env', artifact_dir=SHARED / 'artifacts')


def b_settings():
    return BSettings(model_id=MODEL_ID)


def artifact_store():
    return JsonArtifactStore(SHARED / 'artifacts')


def load_graphs(doc_ids=None):
    st = artifact_store()
    graphs = {}
    for doc_id, version in PINS.items():
        if doc_ids and doc_id not in doc_ids:
            continue
        graph = load_learning_graph(st, doc_id, version)
        modules, learnable = EXPECTED[doc_id]
        if len(graph.modules) != modules or len(graph.learnable_nodes) != learnable:
            raise RuntimeError(f'{doc_id}: graph differs from the pin')
        graphs[doc_id] = graph
    return graphs


def make_runtime():
    runtime = PhaseBRuntime(settings=settings(), b_settings=b_settings(), allow_spend=True, mode='gemini',
                            store_path=STORE_PATH)
    runtime.record_dir = None  # never the shared recordings directory
    if runtime.settings.llm_transport != 'vertex':
        raise RuntimeError('SA-22 requires the configured Vertex transport')
    return runtime


class Capturing(QuizUseCase):
    """QuizUseCase that also keeps a deep copy of every candidate it rejects, at any stage.

    Product code is untouched. `captured` rows are {stage, reason, concept_id, item (full normalized item or None), raw}.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.captured = []
        self._capture_lock = threading.Lock()

    def _record_rejection(self, stage, reason, concept, raw=None, item=None):
        super()._record_rejection(stage, reason, concept, raw, item)
        row = {'stage': stage, 'reason': reason, 'concept_id': concept.get('node_id'),
               'item': copy.deepcopy(item) if item and 'options' in item else None,
               'raw': copy.deepcopy(raw) if raw and not (item and 'options' in item) else None}
        with self._capture_lock:
            self.captured.append(row)


def use_case(graph, runtime, store, tag, *, llm=True):
    """One fresh use case per concept: the shuffle seed depends only on the concept, so reruns give the same order."""
    seed = int.from_bytes(hashlib.sha256(f"{SEEDS['rng']}:{tag}".encode()).digest()[:8], 'big')
    model = runtime.model('quiz_gen') if llm else None
    verifier = runtime.model('quiz_verify') if llm else None
    return Capturing(graph, store, model, verifier_model=verifier, settings=b_settings(),
                     rng=random.Random(seed), spend_guard=runtime.spend_guard if llm else None, clock=runtime.clock if llm else None)


def learner_view(graph, item, tag):
    """The item as the learner sees it: option ids o1.. in bank order, then QuizUseCase._public_item shuffles them."""
    full = copy.deepcopy(item)
    for index, option in enumerate(full['options'], 1):
        option['option_id'] = f'o{index}'
    seed = int.from_bytes(hashlib.sha256(f"{SEEDS['rng']}:view:{tag}".encode()).digest()[:8], 'big')
    helper = QuizUseCase(graph, None, rng=random.Random(seed))
    return helper._public_item(full), full
