"""A localhost-only contract preview using the standard HTTP server."""
from __future__ import annotations

import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

from doc2roadmap.composition_phase_b import DEVELOPMENT_DOCS


class PreviewServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, runtime, *, port=8765):
        self.runtime = runtime
        super().__init__(('127.0.0.1', port), Handler)


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *_):
        pass

    def _respond(self, data, *, status=200, content_type='application/json; charset=utf-8', filename=None):
        payload = data if isinstance(data, bytes) else (data.encode('utf-8') if isinstance(data, str)
                  else json.dumps(data, ensure_ascii=False).encode('utf-8'))
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'")
        if filename:
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(payload)

    def _origin_ok(self):
        hosts = {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}
        origin = self.headers.get('Origin')
        return self.headers.get('Host') in hosts and (origin is None or origin in {f'http://{host}' for host in hosts})

    def _graph(self, args):
        doc_id = args.get('doc_id', 'doc-1')
        if doc_id not in DEVELOPMENT_DOCS:
            raise ValueError('Trang xem thử chỉ dùng sáu tài liệu phát triển')
        version = args.get('graph_version')
        return self.server.runtime.graph(doc_id, int(version) if version is not None else None)

    def do_GET(self):
        if not self._origin_ok():
            self._respond({'error': 'Nguồn yêu cầu không hợp lệ'}, status=403)
            return
        route = urlparse(self.path)
        args = {key: values[0] for key, values in parse_qs(route.query).items()}
        runtime = self.server.runtime
        try:
            if route.path == '/':
                self._respond(Path(__file__).with_name('phase_b.html').read_bytes(), content_type='text/html; charset=utf-8')
            elif route.path == '/api/docs':
                docs = []
                for doc_id in DEVELOPMENT_DOCS:
                    try:
                        graph = runtime.graph(doc_id)
                    except (FileNotFoundError, ValueError):
                        continue
                    docs.append({'doc_id': doc_id, 'graph_version': graph.graph_version,
                                 'modules': len(graph.modules), 'concepts': len(graph.payload.get('sequence', graph.nodes))})
                self._respond({'mode': runtime.mode, 'documents': docs})
            elif route.path == '/api/roadmap':
                graph = self._graph(args)
                self._respond({'contract_version': 'roadmap-1', 'doc_id': graph.doc_id,
                    'graph_version': graph.graph_version, 'modules': list(graph.modules.values()),
                    'naming_status': 'ready' if graph.payload.get('module_naming_contract') == 'module-1' else 'pending',
                    'nodes': [{'node_id': key, 'name': node.get('display_name') or node.get('name')}
                              for key, node in graph.nodes.items() if node.get('learnable')], 'mode': runtime.mode})
            elif route.path == '/api/source':
                graph = self._graph(args)
                chunk = graph.chunks[args['chunk_id']]
                self._respond({'chunk_id': chunk.chunk_id, 'text': chunk.text, 'page': chunk.page,
                               'section_path': chunk.section_path, 'char_start': chunk.char_start,
                               'char_end': chunk.char_end})
            elif route.path == '/api/history':
                self._respond(runtime.quiz(self._graph(args)).history('local', args.get('doc_id')))
            elif route.path == '/api/quiz-attempt':
                self._respond(runtime.quiz(self._graph(args)).get_attempt(args['attempt_id'], 'local'))
            elif route.path == '/api/usage':
                self._respond(runtime.usage(args.get('doc_id')))
            elif route.path == '/api/document':
                from doc2roadmap.application.phase_b.documents import DocumentUseCase
                use_case = DocumentUseCase(None, runtime.store)
                document_id = args['document_id']
                if not re.fullmatch(r'[a-zA-Z0-9_-]{1,128}', document_id):
                    raise ValueError('Mã tài liệu không hợp lệ')
                if args.get('format') == 'md':
                    self._respond(use_case.export(document_id, owner='local'), content_type='text/markdown; charset=utf-8',
                                  filename=document_id + '.md')
                else:
                    self._respond(use_case.get(document_id, owner='local'))
            elif route.path == '/api/image':
                graph = self._graph(args)
                image_id = args['media_id']
                if not re.fullmatch(r'[0-9a-f]{64}', image_id):
                    raise ValueError('Mã ảnh không hợp lệ')
                root = runtime.settings.artifact_dir / 'phase_b' / 'formula_images' / graph.doc_id
                path = next(iter(root.glob(f'parse-v*/images/{image_id}.png')), None) if root.exists() else None
                if path:
                    image = path.read_bytes()
                else:
                    artifact = runtime.artifacts.load_graph(graph.doc_id, graph.graph_version)
                    chunks = runtime.artifacts.load_chunks(graph.doc_id, artifact.manifest['config']['chunks_version'])
                    image = runtime.artifacts.load_image(graph.doc_id, chunks.manifest['parse_version'], image_id)
                self._respond(image, content_type='image/png')
            else:
                self._respond({'error': 'Không có đường dẫn này'}, status=404)
        except (KeyError, ValueError, FileNotFoundError) as error:
            self._respond({'error': str(error)}, status=400)

    def do_POST(self):
        if not self._origin_ok():
            self._respond({'error': 'Nguồn yêu cầu không hợp lệ'}, status=403)
            return
        stream_started = False
        runtime = self.server.runtime
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 65536:
                raise ValueError('Yêu cầu rỗng hoặc quá lớn')
            args = json.loads(self.rfile.read(length))
            if not isinstance(args, dict):
                raise ValueError('Yêu cầu phải là JSON object')
            route = urlparse(self.path).path
            graph = self._graph(args)
            if route == '/api/submit':
                self._respond(runtime.quiz(graph).submit(args['attempt_id'], 'local', args['answers']))
                return
            if route == '/api/quiz-report':
                self._respond(runtime.quiz(graph).report_question('local', args['attempt_id'], args['item_id']))
                return
            if route == '/api/feedback':
                record_id = uuid4().hex
                runtime.store.put_record('feedback', record_id, {'owner': 'local', 'doc_id': graph.doc_id,
                    'graph_version': graph.graph_version, 'kind': args.get('kind', 'relation'),
                    'source': args.get('source'), 'target': args.get('target'), 'reason': str(args.get('reason', ''))[:2000]})
                self._respond({'saved': True})
                return
            if route not in {'/api/lecture', '/api/quiz', '/api/ask', '/api/create-document'}:
                self._respond({'error': 'Không có đường dẫn này'}, status=404)
                return
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Connection', 'close')
            self.end_headers()
            self.close_connection = True
            stream_started = True

            def emit(event):
                self.wfile.write(('data: ' + json.dumps(event, ensure_ascii=False) + '\n\n').encode('utf-8'))
                self.wfile.flush()

            if route == '/api/lecture':
                runtime.lecture(graph, args['node_id'], on_event=emit, preload_next=True)
            elif route == '/api/quiz':
                result = runtime.quiz(graph).make_quiz(graph.doc_id, args['module_id'], 'local', on_event=emit,
                                                       allow_spend=runtime.allow_spend)
                emit({'event': 'final', 'quiz': result})
            elif route == '/api/ask':
                runtime.assistant(graph).ask(graph.doc_id, graph.graph_version, args.get('session_id', 'preview'),
                    args['module_id'], args['question'], owner='local', client_turn_id=args.get('client_turn_id'),
                    reminders_enabled=args.get('reminders_enabled', True), on_event=emit, allow_spend=runtime.allow_spend)
            else:
                result = runtime.document(graph, args['request'], args['scope'], owner='local')
                emit({'event': 'artifact', 'kind': 'document', 'id': result['document_id']})
                emit({'event': 'final', 'document': result})
        except (BrokenPipeError, ConnectionResetError):
            return
        except Exception as error:
            # Provider errors are described without exposing URLs, credentials or tracebacks.
            message = str(error) if isinstance(error, (ValueError, KeyError, PermissionError)) else 'Không hoàn tất được thao tác; xem nhật ký phía máy chủ.'
            if stream_started:
                try:
                    self.wfile.write(('data: ' + json.dumps({'event': 'error', 'message': message}, ensure_ascii=False) + '\n\n').encode('utf-8'))
                except (BrokenPipeError, ConnectionResetError):
                    pass
            else:
                self._respond({'error': message}, status=400)


def serve(runtime, *, port=8765):
    with PreviewServer(runtime, port=port) as server:
        print(f'Pha B ({runtime.mode}): http://127.0.0.1:{server.server_port}', flush=True)
        server.serve_forever()
