"""SA-20 shared helpers: pinned graphs, read-only store, probe namers, E/L/S/R classification.

Nothing here writes to the shared artifacts directory. Graphs are read from it; every output goes to tmp/ of the worktree.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from doc2roadmap.application.phase_b.naming import NameModulesB, _display, _aliases, _words, clean_title
from doc2roadmap.domain.module_titles import transfer_chunk_sections
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore

WORKTREE = Path(__file__).resolve().parents[2]
SHARED = Path('C:/Users/ngoco/Desktop/Doctoroadmap')
ARTIFACTS = SHARED / 'artifacts'
OUT = WORKTREE / 'tmp/sa20'
MODEL_ID = 'gemini-3.1-flash-lite'
# Pinned graphs (plan table, evaluation round 20-23): named Phase B graph version per book.
PINS = {'doc-1': 8, 'nhap-mon-ml': 50, 'naive-bayes': 49, 'doc-6': 29, 'xstk-ch3-1': 68, 'doc-4': 27}
EXPECTED_MODULES = {'doc-1': 35, 'nhap-mon-ml': 15, 'naive-bayes': 5, 'doc-6': 2, 'xstk-ch3-1': 14, 'doc-4': 91}


class ReadOnlyStore:
    """Delegates reads to the shared store; save_graph keeps the result in memory only."""
    def __init__(self, inner):
        self._inner = inner

    def __getattr__(self, name):
        if name.startswith(('save_', 'clear_')):
            raise PermissionError('SA-20 never writes to the shared artifacts directory')
        return getattr(self._inner, name)

    def save_graph(self, doc_id, source_hash, config_hash, config, payload, *, upstream_version=None,
                   manifest_fields=None):
        return SimpleNamespace(path=None, payload=payload, version=None, manifest={'config': config})


def store():
    return ReadOnlyStore(JsonArtifactStore(ARTIFACTS))


def load_pinned(st=None):
    """Returns {doc_id: (named, upstream)} after checking the pin claims against manifests."""
    st = st or store()
    result = {}
    for doc_id, version in PINS.items():
        named = st.load_graph(doc_id, version)
        config = named.manifest['config']
        if (named.payload.get('module_naming_contract') != 'module-1'
                or not config.get('algorithm_id', '').startswith('phase-b-module-names-')):
            raise RuntimeError(f'{doc_id} v{version} is not a Phase B named graph')
        upstream = st.load_graph(doc_id, named.manifest['upstream_version'])
        if (len(named.payload['modules']) != EXPECTED_MODULES[doc_id]
                or len(upstream.payload['modules']) != len(named.payload['modules'])):
            raise RuntimeError(f'{doc_id}: module count differs from the pin')
        result[doc_id] = (named, upstream)
    return result


class Probe(NameModulesB):
    """Experiment-only namer. Options live in the script, product code is untouched.

    drop_neighbors: L2, the request carries no neighbor modules.
    hide_author: module ids whose own section title is hidden from the request (parent titles stay).
    """
    def __init__(self, *args, drop_neighbors=False, hide_author=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.drop_neighbors, self.hide_author = drop_neighbors, set(hide_author)
        self.hidden_log = {}

    def _prepare(self, doc_id, upstream):
        chunks, prepared = super()._prepare(doc_id, upstream)
        nodes = {n['node_id']: n for n in upstream.payload['nodes']}
        chunk_text = {c.chunk_id: c.text for c in chunks.result.chunks}
        rows = []
        for module, fallback, data, vocabulary, fragments in prepared:
            data = dict(data)
            if self.drop_neighbors:
                data.pop('neighbors')
            if module['module_id'] in self.hide_author and data['author_path']:
                hidden = data['author_path'][-1]
                data['author_path'] = data['author_path'][:-1]
                data['exact_author_section'] = False
                data['candidates'] = [c for c in data['candidates'] if c['title'].casefold() != hidden.casefold()]
                # words that only the hidden title supplies must not stay in the vocabulary lists either
                other = set(_words(' '.join(data['author_path'])))
                for nid in module['node_ids']:
                    node = nodes[nid]
                    other.update(w for t in [node.get('name', ''), _display(node), node.get('description', ''),
                                             *_aliases(node)] for w in _words(t))
                    for cid in node.get('teaching_chunk_ids', []):
                        other.update(_words(chunk_text.get(cid, '')))
                removed = set(_words(hidden)) - other
                data['content_vocabulary'] = sorted(set(data['content_vocabulary']) - removed)
                vocabulary = set(vocabulary) - removed
                fragments = set(fragments) - {hidden}
                self.hidden_log[module['module_id']] = {'hidden': hidden, 'removed_words': sorted(removed)}
            rows.append((module, fallback, data, vocabulary, fragments))
        return chunks, rows


def classify_modules(st, doc_id, upstream):
    """E/L/S/R per section 2.1 of the naming report, on the same section assignment NameModulesB uses.

    common = deepest section shared by every concept of the module.
    R: no common section (only the root). E: the module's concept set equals every concept taught in that section
    (and its sub-sections). L: not E and all concepts sit in that one section. S: not E and the concepts span two or
    more sub-sections. Returns {module_id: {'type', 'section_id', 'section_title'}}.
    """
    config = upstream.manifest['config']
    chunks = st.load_role_chunks(doc_id, config['chunks_version'])
    version = config.get('title_sections_version') or (chunks.manifest.get('role_transfer') or {}).get('reference_version')
    reference = st.load_chunks(doc_id, version) if version and version != chunks.version else chunks
    sections = {s.section_id: s for s in reference.result.sections}
    chunk_by_id = {c.chunk_id: c for c in chunks.result.chunks}
    transferred = (transfer_chunk_sections(chunks.result.chunks, reference.result.chunks)
                   if reference is not chunks else {})
    nodes = {n['node_id']: n for n in upstream.payload['nodes']}
    section_of = {}
    for module in upstream.payload['modules']:
        declared = module.get('title_section_ids') or []
        for i, node_id in enumerate(module['node_ids']):
            source = sorted((chunk_by_id[cid] for cid in nodes[node_id].get('teaching_chunk_ids', [])
                             if cid in chunk_by_id), key=lambda c: c.order_index)
            section_of[node_id] = (declared[i] if i < len(declared) else
                                  transferred.get(source[0].chunk_id, source[0].parent_section_id)
                                  if source else None)

    def path(section_id):
        out, seen = [], set()
        while section_id in sections and section_id not in seen:
            seen.add(section_id)
            out.append(section_id)
            section_id = sections[section_id].parent_section_id
        return out[::-1]

    result = {}
    for module in upstream.payload['modules']:
        ids = module['node_ids']
        paths = [path(section_of.get(nid)) for nid in ids]
        common = []
        for group in zip(*paths):
            if len(set(group)) != 1:
                break
            common.append(group[0])
        common_id = common[-1] if common else None
        if common_id is None:
            kind = 'R'
        else:
            own = {nid for nid, sid in section_of.items() if common_id in path(sid)}
            if set(ids) == own:
                kind = 'E'
            elif all(section_of.get(nid) == common_id for nid in ids):
                kind = 'L'
            else:
                kind = 'S'
        result[module['module_id']] = {'type': kind, 'section_id': common_id,
                                       'section_title': clean_title(sections[common_id].title)[0] if common_id else None}
    return result
