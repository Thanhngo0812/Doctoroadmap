"""CLI wiring for Phase B; behavior belongs to the public use cases."""
from __future__ import annotations

import json
from pathlib import Path

from doc2roadmap.composition_phase_b import PhaseBRuntime
from doc2roadmap.domain.phase_b_limits import BSettings


def configure(commands):
    phase = commands.add_parser('phase-b', help='bài giảng, quiz và trợ lý theo hợp đồng Pha B')
    actions = phase.add_subparsers(dest='b_action', required=True)
    for name in ('names', 'a12', 'lookup', 'search', 'graph-tool', 'concept-index', 'formulas', 'lecture',
                 'quiz', 'submit', 'history', 'report-question', 'ask', 'document', 'usage', 'lecture-diagnostics', 'serve'):
        command = actions.add_parser(name)
        command.add_argument('--doc-id', required=name not in {'usage', 'lecture-diagnostics', 'serve'})
        command.add_argument('--graph-version', type=int)
        command.add_argument('--allow-spend', action='store_true')
        command.add_argument('--dry-run', action='store_true')
        command.add_argument('--mode', choices=('offline', 'gemini'))
        command.add_argument('--settings', type=Path)
        command.add_argument('--owner', default='local')
        command.add_argument('--store', type=Path)
        command.add_argument('--record-dir', type=Path)
        command.add_argument('--replay-dir', type=Path)
        if name == 'names':
            command.add_argument('--deterministic', action='store_true')
        if name in {'lookup', 'search', 'ask'}:
            command.add_argument('question')
        if name == 'graph-tool':
            command.add_argument('tool', choices=('lookup_concept', 'get_module_info', 'why_here', 'path_to', 'traverse', 'get_media'))
            command.add_argument('value')
            command.add_argument('--edge-type', default='requires')
            command.add_argument('--direction', choices=('in', 'out'), default='out')
        if name == 'lecture':
            command.add_argument('--node-id', action='append', required=True)
            command.add_argument('--deterministic', action='store_true')
            command.add_argument('--preload-next', action='store_true')
        if name in {'quiz', 'search', 'ask'}:
            command.add_argument('--module-id', required=name == 'ask')
        if name == 'search':
            command.add_argument('--k', type=int, default=5)
        if name == 'quiz':
            command.add_argument('--node-id', action='append')
            command.add_argument('--n', type=int)
            command.add_argument('--level')
        if name in {'submit', 'report-question'}:
            command.add_argument('--attempt-id', required=True)
        if name == 'submit':
            command.add_argument('--answers', type=Path, required=True)
        if name == 'report-question':
            command.add_argument('--item-id', required=True)
        if name == 'ask':
            command.add_argument('--session-id', default='cli')
            command.add_argument('--client-turn-id')
        if name == 'document':
            command.add_argument('request')
            command.add_argument('--scope', required=True)
            command.add_argument('--output', type=Path)
        if name == 'formulas':
            command.add_argument('--pdf', type=Path, required=True)
        if name == 'serve':
            command.add_argument('--port', type=int, default=8765)


def run(args):
    values = json.loads(args.settings.read_text(encoding='utf-8')) if args.settings else {}
    mode = args.mode or ('gemini' if args.allow_spend or args.dry_run or args.replay_dir else 'offline')
    runtime = PhaseBRuntime(b_settings=BSettings(**values), allow_spend=args.allow_spend and not args.dry_run,
                            store_path=args.store, mode=mode, record_dir=args.record_dir, replay_dir=args.replay_dir)
    action = args.b_action
    if action == 'serve':
        from doc2roadmap.presentation.preview.server import serve
        if args.dry_run:
            return {'dry_run': True, 'host': '127.0.0.1', 'port': args.port, 'mode': mode}
        serve(runtime, port=args.port)
        return {}
    if action == 'usage':
        return runtime.usage(args.doc_id)
    if action == 'lecture-diagnostics':
        from doc2roadmap.application.phase_b.lectures import summarize_lecture_diagnostics
        return summarize_lecture_diagnostics(runtime.store.usage_rows(args.doc_id), doc_id=args.doc_id)
    if action == 'names':
        return runtime.naming(args.doc_id, graph_version=args.graph_version,
                              deterministic=args.deterministic, dry_run=args.dry_run)
    if action == 'a12':
        return runtime.a12(args.doc_id, graph_version=args.graph_version, dry_run=args.dry_run)
    graph = runtime.graph(args.doc_id, args.graph_version)
    if action == 'graph-tool':
        method = getattr(graph, args.tool)
        if args.tool == 'why_here':
            return method(args.value, settings=runtime.b_settings)
        return (method(args.value, args.edge_type, args.direction) if args.tool == 'traverse' else method(args.value))
    if action == 'lookup':
        if args.dry_run:
            return {'dry_run': True, **graph.lookup_concept(args.question)}
        return runtime.lookup(graph, args.question)
    if action == 'search':
        if args.dry_run:
            return {'dry_run': True, 'embedding_calls_estimate': int(mode == 'gemini'),
                    'estimated_input_tokens': (len(args.question) + 2) // 3}
        return {'hits': runtime.search(graph, args.question, k=args.k, current_module_id=args.module_id)}
    if action == 'concept-index':
        from doc2roadmap.application.phase_b.concept_index import IndexConcepts
        from doc2roadmap.infrastructure.embedding.gemini import GeminiEmbedding
        settings = runtime.settings
        embedding = GeminiEmbedding(settings.gemini_api_key.get_secret_value() if settings.gemini_api_key else 'dry-run-no-key',
            model=settings.embedding_model_id, output_dimensionality=settings.embedding_dimensions,
            transport=settings.llm_transport, vertex_project=settings.vertex_project, vertex_location=settings.vertex_location)
        return IndexConcepts(runtime.artifacts, embedding, runtime.store).execute(
            args.doc_id, graph.graph_version, dry_run=args.dry_run, allow_spend=args.allow_spend and not args.dry_run)
    if action == 'lecture':
        results = [runtime.lecture(graph, node_id, dry_run=args.dry_run, deterministic=args.deterministic,
                                  preload_next=args.preload_next) for node_id in args.node_id]
        return results[0] if len(results) == 1 else {'lectures': results}
    if action == 'quiz':
        return runtime.quiz(graph).make_quiz(args.doc_id, args.module_id, args.owner,
            node_ids=args.node_id, n=args.n, level=args.level, dry_run=args.dry_run,
            allow_spend=(args.allow_spend or bool(args.replay_dir)) and not args.dry_run)
    if action == 'submit':
        return runtime.quiz(graph).submit(args.attempt_id, args.owner, json.loads(args.answers.read_text(encoding='utf-8')))
    if action == 'history':
        return runtime.quiz(graph).history(args.owner, args.doc_id)
    if action == 'report-question':
        return runtime.quiz(graph).report_question(args.owner, args.attempt_id, args.item_id)
    if action == 'ask':
        return runtime.assistant(graph).ask(args.doc_id, graph.graph_version, args.session_id, args.module_id,
            args.question, owner=args.owner, client_turn_id=args.client_turn_id, dry_run=args.dry_run,
            allow_spend=args.allow_spend and not args.dry_run)
    if action == 'document':
        document = runtime.document(graph, args.request, args.scope, owner=args.owner, dry_run=args.dry_run)
        if args.output and not args.dry_run and document.get('status') == 'ready':
            from doc2roadmap.application.phase_b.documents import export_markdown
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(export_markdown(document), encoding='utf-8')
        return document
    if action == 'formulas':
        from doc2roadmap.application.phase_b.formula_images import CutFormulaImages, persist_formula_images
        from doc2roadmap.infrastructure.media.formula_images import PdfiumFormulaRenderer
        if args.dry_run:
            return {'dry_run': True, 'formula_count': sum(node.node_type == 'formula' for node in graph.tree.nodes), 'usd': 0}
        result = CutFormulaImages(PdfiumFormulaRenderer()).execute(args.pdf, graph.tree)
        artifact = runtime.artifacts.load_graph(args.doc_id, graph.graph_version)
        chunks = runtime.artifacts.load_chunks(args.doc_id, artifact.manifest['config']['chunks_version'])
        return persist_formula_images(result, runtime.settings.artifact_dir, args.doc_id, chunks.manifest['parse_version'])
    raise ValueError('Lệnh Pha B không được hỗ trợ')
