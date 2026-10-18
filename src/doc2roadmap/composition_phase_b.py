"""Composition of the learner-facing use cases; providers stay outside application."""
from functools import partial
from dataclasses import asdict
from pathlib import Path
from statistics import median
from uuid import uuid4

from doc2roadmap.application.phase_b.assistant import AssistantUseCase
from doc2roadmap.application.phase_b.documents import DocumentUseCase
from doc2roadmap.application.phase_b.lectures import LectureUseCase
from doc2roadmap.application.phase_b.naming import NameModulesB
from doc2roadmap.application.phase_b.quiz import QuizUseCase
from doc2roadmap.application.phase_b.retrieval import (
    SearchDocumentB, assert_retrieval_compatible, build_module_assignments, load_learning_graph,
)
from doc2roadmap.application.use_cases.index_document import retriever_from_payload
from doc2roadmap.config import Settings
from doc2roadmap.domain.phase_b_limits import BSettings, context_hash
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore
from doc2roadmap.infrastructure.artifacts.phase_b_store import JsonPhaseBStore
from doc2roadmap.infrastructure.embedding.gemini import GeminiEmbedding
from doc2roadmap.infrastructure.llm.phase_b import GeminiToolModel, RecordingToolModel, ReplayToolModel
from doc2roadmap.infrastructure.llm.phase_b_demo import DemoModel


DEVELOPMENT_DOCS = ('doc-1', 'nhap-mon-ml', 'naive-bayes', 'doc-6', 'xstk-ch3-1', 'doc-4')


class PhaseBRuntime:
    def __init__(self, *, settings=None, b_settings=None, allow_spend=False, store_path=None, mode=None,
                 record_dir=None, replay_dir=None):
        self.settings = settings or Settings()
        self.b_settings = b_settings or BSettings()
        self.allow_spend = allow_spend
        self.artifacts = JsonArtifactStore(self.settings.artifact_dir)
        root = self.settings.artifact_dir / 'phase_b'
        self.mode = mode or ('gemini' if allow_spend else 'offline')
        if self.mode not in {'gemini', 'offline'}:
            raise ValueError('mode phải là gemini hoặc offline')
        self.store = JsonPhaseBStore(store_path or root / ('live.json' if self.mode == 'gemini' else 'offline.json'))
        if record_dir and replay_dir:
            raise ValueError('Chọn một trong record_dir và replay_dir')
        self.record_dir = record_dir or (root / 'recordings' / uuid4().hex if allow_spend else None)
        self.replay_dir = replay_dir
        self._models = {}

    def model(self, purpose):
        if purpose in self._models:
            return self._models[purpose]
        prompt_hash = context_hash(['phase-b-v1', purpose, asdict(self.b_settings)])
        if self.replay_dir:
            model = ReplayToolModel(Path(self.replay_dir) / (purpose + '.json'), prompt_hash=prompt_hash)
            self._models[purpose] = model
            return model
        if self.mode == 'offline':
            return DemoModel()
        outputs = {'module_title': self.b_settings.naming_max_output_tokens,
                   'lecture': self.b_settings.lecture_max_output_tokens,
                   'assistant': self.b_settings.assistant_max_output_tokens,
                   'document': self.b_settings.document_max_output_tokens,
                   'quiz_gen': self.b_settings.quiz_generation_max_output_tokens,
                   'quiz_verify': self.b_settings.quiz_verifier_max_output_tokens}
        temperature = {'module_title': self.b_settings.naming_temperature,
                       'lecture': self.b_settings.lecture_temperature,
                       'document': self.b_settings.document_temperature}.get(purpose, 1.0 if purpose == 'assistant' else 0.0)
        model = GeminiToolModel(
            self.settings.gemini_api_key.get_secret_value() if self.settings.gemini_api_key else 'dry-run-no-key',
            self.b_settings.model_id, transport=self.settings.llm_transport,
            vertex_project=self.settings.vertex_project, vertex_location=self.settings.vertex_location,
            temperature=temperature, max_output_tokens=outputs[purpose],
            timeout_seconds=self.settings.gemini_timeout_seconds)
        if self.record_dir:
            model = RecordingToolModel(model, Path(self.record_dir) / (purpose + '.json'), prompt_hash=prompt_hash)
        self._models[purpose] = model
        return model

    def graph(self, doc_id, graph_version=None):
        graph = load_learning_graph(self.artifacts, doc_id, graph_version)
        if not graph.modules:
            raise ValueError('Phiên bản đồ thị chưa có module A10; chọn --graph-version đã hoàn tất')
        return graph

    def naming(self, doc_id, *, graph_version=None, deterministic=False, dry_run=False):
        graph = self.graph(doc_id, graph_version)
        upstream = self.artifacts.load_graph(doc_id, graph.graph_version)
        # A repeated default command keeps the A10 context used for the first naming pass.
        # An explicit version intentionally permits a different neighbor-title context.
        while graph_version is None and upstream.payload.get('module_naming_contract') == 'module-1':
            config = upstream.manifest['config']
            if not config.get('algorithm_id', '').startswith('phase-b-module-names-'):
                break
            source_version = config.get('upstream_version')
            if not isinstance(source_version, int) or not 0 < source_version < upstream.version:
                raise ValueError('Artifact đặt tên thiếu phiên bản A10 đầu vào hợp lệ')
            upstream = self.artifacts.load_graph(doc_id, source_version)
        use_case = NameModulesB(self.artifacts, self.model('module_title'), phase_b_store=self.store,
                               settings=self.b_settings, deterministic=deterministic or self.mode == 'offline',
                               allow_spend=self.allow_spend or self.mode == 'offline' or bool(self.replay_dir), concurrency=4)
        if dry_run:
            return {'doc_id': doc_id, 'source_graph_version': upstream.version, 'dry_run': True,
                    **use_case.plan(doc_id, upstream=upstream).to_dict()}
        artifact, reused = use_case.execute(doc_id, upstream=upstream)
        return {'doc_id': doc_id, 'source_graph_version': upstream.version,
                'graph_version': artifact.version, 'reused': reused,
                'modules': artifact.payload['modules'], 'path': str(artifact.path)}

    def a12(self, doc_id, *, graph_version=None, dry_run=False):
        graph = self.graph(doc_id, graph_version)
        index = self.artifacts.load_latest_retrieval(doc_id)
        fingerprint = assert_retrieval_compatible(index.payload, list(graph.chunks.values()))
        result = build_module_assignments(graph.payload, list(graph.chunks.values()))
        result.update(doc_id=doc_id, graph_version=graph.graph_version, retrieval_version=index.version,
                      input_fingerprint=fingerprint)
        if not dry_run:
            self.store.put_record('module_assignment', context_hash([doc_id, graph.graph_version, index.version]), result)
        return {**result, 'dry_run': dry_run}

    def search(self, graph, query, *, scope='ưu tiên module', k=6, current_module_id=None):
        if self.allow_spend:
            embedding = GeminiEmbedding(
                self.settings.gemini_api_key.get_secret_value() if self.settings.gemini_api_key else None,
                model=self.b_settings.embedding_model_id, output_dimensionality=768,
                transport=self.settings.llm_transport, vertex_project=self.settings.vertex_project,
                vertex_location=self.settings.vertex_location)
            return SearchDocumentB(self.artifacts, embedding, self.store).search(
                query, doc_id=graph.doc_id, graph_version=graph.graph_version, current_module_id=current_module_id,
                scope=scope, k=k, allow_spend=True)
        index = self.artifacts.load_latest_retrieval(graph.doc_id)
        assert_retrieval_compatible(index.payload, list(graph.chunks.values()))
        retriever = retriever_from_payload(index.payload)
        hits = retriever.search_bm25(query, top_k=20)
        overlay = build_module_assignments(graph.payload, list(graph.chunks.values()))['assignments']
        eligible, global_best = [], []
        for i, hit in enumerate(hits):
            assignment = overlay[hit.chunk_id]
            relation = graph.relation(assignment['module_id'], current_module_id)
            row = {'chunk_id': hit.chunk_id, 'text': hit.document.text, 'page': hit.document.page,
                   'score': hit.score, **assignment, 'relation': relation}
            if relation in {'dang_mo', 'truoc'}:
                eligible.append(row)
            if i < 5:
                global_best.append(row)
        selected, seen = [], set()
        for row in [*eligible[:3], *global_best[:2], *global_best, *eligible,
                    *({'chunk_id': h.chunk_id, 'text': h.document.text, 'page': h.document.page,
                       'relation': 'khong_ro', 'score': h.score} for h in hits)]:
            if row['chunk_id'] not in seen:
                selected.append(row)
                seen.add(row['chunk_id'])
            if len(selected) >= min(k, 6):
                break
        return selected

    def lecture(self, graph, node_id, *, dry_run=False, on_event=None, preload_next=False, deterministic=False):
        model = None if deterministic else self.model('lecture')
        return LectureUseCase(model, self.store, settings=self.b_settings).make(
            graph.doc_id, graph.graph_version, graph, node_id, dry_run=dry_run,
            allow_spend=self.allow_spend or self.mode == 'offline' or bool(self.replay_dir), on_event=on_event, preload_next=preload_next)

    def quiz(self, graph):
        model = self.model('quiz_gen') if self.mode == 'gemini' else None
        verifier = self.model('quiz_verify') if self.mode == 'gemini' else None
        return QuizUseCase(graph, self.store, model, settings=self.b_settings, verifier_model=verifier)

    def document(self, graph, request, scope, *, owner='local', dry_run=False):
        retriever = None
        if self.allow_spend and self.mode == 'gemini':
            embedding = GeminiEmbedding(
                self.settings.gemini_api_key.get_secret_value() if self.settings.gemini_api_key else None,
                model=self.b_settings.embedding_model_id, output_dimensionality=768,
                transport=self.settings.llm_transport, vertex_project=self.settings.vertex_project,
                vertex_location=self.settings.vertex_location)
            retriever = SearchDocumentB(self.artifacts, embedding, self.store)
        return DocumentUseCase(self.model('document'), self.store, settings=self.b_settings, retriever=retriever).create(
            graph.doc_id, graph.graph_version, graph, request, scope, owner=owner, dry_run=dry_run,
            allow_spend=self.allow_spend or self.mode == 'offline' or bool(self.replay_dir))

    def assistant(self, graph):
        def get_lecture(concept, **kwargs):
            return self.lecture(graph, concept)

        def make_quiz(scope, n=None, level=None, *, owner, **kwargs):
            return self.quiz(graph).make_quiz(graph.doc_id, None, owner, n=n, scope=scope,
                                              level=level, origin='assistant', allow_spend=self.allow_spend)

        def make_document(request, scope, *, owner, **kwargs):
            return self.document(graph, request, scope, owner=owner)
        return AssistantUseCase(graph, self.store, self.model('assistant'), settings=self.b_settings,
                                search=partial(self.search, graph), concept_lookup=partial(self.lookup, graph), lecture=get_lecture,
                                quiz=make_quiz, document=make_document)

    def lookup(self, graph, query):
        named = graph.lookup_concept(query)
        if named['matches'] or self.mode == 'offline' or not self.allow_spend:
            return named
        from doc2roadmap.application.phase_b.concept_index import IndexConcepts
        embedding = GeminiEmbedding(
            self.settings.gemini_api_key.get_secret_value() if self.settings.gemini_api_key else None,
            model=self.b_settings.embedding_model_id, output_dimensionality=768,
            transport=self.settings.llm_transport, vertex_project=self.settings.vertex_project,
            vertex_location=self.settings.vertex_location)
        use_case = IndexConcepts(self.artifacts, embedding, self.store)
        index = use_case.execute(graph.doc_id, graph.graph_version, allow_spend=True)
        return {'matches': use_case.lookup(index, query, allow_spend=True)}

    def usage(self, doc_id=None):
        groups = {}
        for row in self.store.usage_rows(doc_id):
            group = groups.setdefault(row['purpose'], {'calls': 0, 'usd': 0, 'input_tokens': 0,
                                                       'output_tokens': 0, 'thought_tokens': 0, 'times_ms': []})
            group['calls'] += 1
            group['usd'] += row.get('cost_usd', 0)
            for key in ('input_tokens', 'output_tokens', 'thought_tokens'):
                group[key] += row.get(key, 0)
            group['times_ms'].append(row.get('elapsed_ms', 0))
        for group in groups.values():
            times = sorted(group.pop('times_ms'))
            group.update(p50_ms=median(times), p90_ms=times[min(len(times) - 1, int(.9 * len(times)))])
        return {'doc_id': doc_id, 'mode': self.mode, 'purposes': groups,
                'total_usd': sum(group['usd'] for group in groups.values())}
