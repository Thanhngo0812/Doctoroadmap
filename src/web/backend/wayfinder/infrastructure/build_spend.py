"""Per-attempt Vertex reservation, adapted from the W-13 recovery BudgetGuard.

Global standard prices: cloud.google.com/vertex-ai/generative-ai/pricing.
Generation reserves the full 1,048,576 context plus 65,536 output tokens,
including images/thinking. Embedding reserves its documented 2,048-token limit.
This deliberately conservative bound is not a forecast of book cost.
"""
from decimal import Decimal
from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from threading import Condition, Lock
from time import perf_counter
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import urlopen
from unittest.mock import patch

_operator_run_lock = Lock()


class BuildSpendStopped(Exception):
    """Must propagate through model-job repair handlers that catch RuntimeError."""


class BuildSpendGuard:
    def __init__(self, limit, provider, *, log=None):
        self.limit = Decimal(str(limit))
        if not self.limit.is_finite() or self.limit <= 0:
            raise ValueError('The approved budget must be positive and finite')
        self.provider, self.condition = provider, Condition()
        self.log = log
        self.known = self.held = self.unknown = Decimal(0)
        self.calls, self.stopped, self.events = 0, False, []
        self.audit_failed = False
        self.stage, self.embedding_spans = 'doc_reading', []

    def embedding_wait(self, stage):
        total, end = 0.0, 0.0
        for start, stop in sorted((a, b) for step, a, b in self.embedding_spans if step == stage):
            total += max(0.0, stop - max(start, end))
            end = max(end, stop)
        return total

    def bound(self, request):
        url = urlsplit(request.full_url)
        if url.scheme != 'https' or url.netloc != 'aiplatform.googleapis.com' or '/locations/global/' not in url.path:
            raise BuildSpendStopped('Only the approved Vertex global transport is priced')
        payload = json.loads(request.data)
        if url.path.endswith('/models/gemini-embedding-001:predict'):
            if len(payload.get('instances', [])) != 1:
                raise BuildSpendStopped('Vertex embedding accepts one text per request')
            return Decimal('0.0003072')
        if (not url.path.endswith('/models/gemini-3.1-flash-lite:generateContent')
                or set(payload) - {'systemInstruction', 'contents', 'generationConfig'}):
            raise BuildSpendStopped('Model, operation or additional service is outside the approved price profile')
        if not 0 < payload.get('generationConfig', {}).get('maxOutputTokens', 0) <= 65536:
            raise BuildSpendStopped('Output limit is outside the documented model limit')
        for content in payload.get('contents', []) + [payload.get('systemInstruction', {})]:
            for part in content.get('parts', []):
                if 'fileData' in part or ('inlineData' in part and not part['inlineData'].get('mimeType', '').startswith('image/')):
                    raise BuildSpendStopped('Only text and inline images are included in the approved price profile')
        return Decimal('0.360448')

    def _reserve(self, value):
        with self.condition:
            while True:
                if self.stopped or self.unknown:
                    raise BuildSpendStopped('Usage is unknown or a provider bound was exceeded; stop dispatch')
                if value > self.limit:
                    self.stopped = True
                    raise BuildSpendStopped('One request exceeds the approved budget')
                if self.known + self.held + value <= self.limit:
                    self.held += value
                    return
                if not self.held:
                    self.stopped = True
                    raise BuildSpendStopped('Next request exceeds the approved remaining budget')
                self.condition.wait()

    def snapshot(self):
        with self.condition:
            return {**{key: format(value.normalize(), 'f') for key, value in {
                'limit_usd': self.limit, 'known_usd': self.known, 'held_usd': self.held,
                'unknown_upper_usd': self.unknown}.items()}, 'http_calls': self.calls, 'stopped': self.stopped,
                    'audit_failed': self.audit_failed}

    def __call__(self, request, *args, **kwargs):
        reserved = self.bound(request)
        self._reserve(reserved)
        actual = None
        try:
            with self.condition:
                self.calls += 1
            with self.provider(request, *args, **kwargs) as response:
                raw = response.read()
            payload = json.loads(raw)
            if request.full_url.endswith(':predict'):
                usage = payload['predictions'][0]['embeddings'].get('statistics', {})
                counts, rates = [usage.get('token_count')], [Decimal('.15')]
            else:
                usage = payload.get('usageMetadata', {})
                counts = [usage.get('promptTokenCount'), usage.get('candidatesTokenCount'), usage.get('thoughtsTokenCount', 0)]
                rates = [Decimal('.25'), Decimal('1.50'), Decimal('1.50')]
            if all(not isinstance(n, bool) and isinstance(n, (int, float)) and n >= 0 and int(n) == n for n in counts):
                actual = sum(Decimal(str(n)) * rate for n, rate in zip(counts, rates, strict=True)) / 1_000_000
            return BytesIO(raw)
        except HTTPError as error:
            if error.code != 200:
                actual = Decimal(0)
            raise
        finally:
            with self.condition:
                self.held -= reserved
                if actual is None:
                    self.unknown += reserved
                else:
                    self.known += actual
                    self.stopped |= actual > reserved
                event = {'stage': self.stage, 'reserved_usd': str(reserved),
                         'actual_usd': None if actual is None else str(actual), 'budget': self.snapshot()}
                self.events.append(event)
                try:
                    if self.log is not None:
                        with self.log.open('a', encoding='utf-8') as handle:
                            handle.write(json.dumps(event) + '\n')
                except OSError:
                    self.stopped = True
                    self.audit_failed = True
                    # Return this already-billed response so the core meter retains its usage.
                    # Further dispatch is stopped, and the terminal receipt is failed below.
                finally:
                    self.condition.notify_all()


@dataclass(frozen=True)
class BuildSpendApproval:
    """Trusted operator input, created only after the owner's exact-run approval.

    No HTTP endpoint or WebSettings field can construct this grant. Its reference
    is consumed once in the same PostgreSQL store as the build, including failures.
    """
    reference: str
    file_sha256: str
    pipeline_version: str
    max_usd: str
    audit_log: Path | None = None

    @contextmanager
    def activate(self, path, doc_id, runtime):
        digest = sha256(path.read_bytes()).hexdigest()
        if (not self.reference.strip() or digest != self.file_sha256 or doc_id != 'u-' + digest[:20]
                or runtime.pipeline_version != self.pipeline_version):
            raise ValueError('Approval does not match this file, document or pipeline')
        settings = runtime.settings
        if settings.vertex_location != 'global' or settings.embedding_model_id != 'gemini-embedding-001' or any(
                getattr(settings, field) != 'gemini-3.1-flash-lite' for field in
                ('extraction_model_id', 'merge_model_id', 'description_model_id', 'roadmap_model_id')):
            raise ValueError('Approval requires the verified Vertex global price profile')
        guard = BuildSpendGuard(self.max_usd, urlopen, log=self.audit_log)
        store = runtime.phase_b_store
        record = dict(reference=self.reference, doc_id=doc_id, file_sha256=digest,
                      pipeline_version=self.pipeline_version, max_usd=self.max_usd, state='consumed')
        with store.atomic():
            if store.get_record('w15_build_approval', self.reference) is not None:
                raise ValueError('Approval was already consumed')
            store.put_record('w15_build_approval', self.reference, record)
        from doc2roadmap.infrastructure.embedding.gemini import GeminiEmbedding
        original = GeminiEmbedding._embed_vertex

        def observe_embedding(adapter, item):
            stage, started = guard.stage, perf_counter()
            try:
                return original(adapter, item)
            finally:
                with guard.condition:
                    guard.embedding_spans.append((stage, started, perf_counter()))

        try:
            # One dedicated operator worker process; serialize transport hooks in-process.
            with _operator_run_lock, patch('doc2roadmap.infrastructure.llm.gemini.urlopen', guard), \
                    patch('doc2roadmap.infrastructure.embedding.gemini.urlopen', guard), \
                    patch('doc2roadmap.infrastructure.llm.phase_b.urlopen', guard), \
                    patch.object(GeminiEmbedding, '_embed_vertex', observe_embedding):
                yield guard
        finally:
            store.put_record('w15_build_approval', self.reference,
                             {**record, 'state': 'finished', 'budget': guard.snapshot(), 'events': guard.events})
